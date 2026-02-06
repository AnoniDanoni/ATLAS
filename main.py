# -*- coding: utf-8 -*-
# main.py - Aplicação principal ATLAS

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
import os
import copy
from datetime import datetime

import set as set_module
from loading_screen import tela_carregamento

from core import (
    DIRETORIO_ATLAS, CONFIG_FILE,
    carregar_config, salvar_config, 
    obter_pastas_sessao, atualizar_pastas_sessao,
    detectar_versoes_revit, abrir_revit,
    verificar_atualizacoes, extrair_nome_base
)

from ui import (
    JanelaSelecaoRevit, JanelaSelecaoPastas,
    JanelaGerenciarSessoes, JanelaGerenciarPastas
)


# ==================== JANELA DE RELATÓRIO ====================

class JanelaRelatorio(tk.Toplevel):
    def __init__(self, parent, config, resultados, bg_principal, bg_secundario, fg_texto, fg_texto_secundario, 
                 filter_novos, filter_desatualizados, filter_atualizados):
        super().__init__(parent)
        self.title("📊 Relatório")
        self.geometry("1000x700")
        self.configure(bg=bg_principal)
        self.resizable(True, True)
        self.grab_set()
        
        self.parent = parent
        self.config = config
        self.resultados = resultados
        self.bg_principal = bg_principal
        self.bg_secundario = bg_secundario
        self.bg_terciario = "#282B30"
        self.fg_texto = fg_texto
        self.fg_texto_secundario = fg_texto_secundario
        self.cor_acento = "#FFFFFF"
        self.cor_novo = "#4D8AC8"
        self.cor_desatualizado = "#954EF1"
        self.cor_atualizado = "#5865F2"
        
        self.filter_novos = filter_novos
        self.filter_desatualizados = filter_desatualizados
        self.filter_atualizados = filter_atualizados
        
        # Dicionário para armazenar valores dos comboboxes por arquivo
        self.combo_values = {}
        
        # Filtro visual (qual tipo de arquivo mostrar)
        self.filtro_visual = 'todos'
        
        # Dicionário para rastrear widgets de items
        self.item_widgets = {}
        
        self._montar_interface()
        self._preencher_lista_unica()
        
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")

    def _montar_interface(self):
        """Monta a interface da janela de relatório"""
        frame_superior = tk.Frame(self, bg=self.bg_secundario)
        frame_superior.pack(fill="x", padx=0, pady=0)
        
        ttk.Label(frame_superior, text="📊 Relatório de Atualizações", 
                 font=("Segoe UI", 12, "bold"), background=self.bg_secundario, 
                 foreground=self.cor_acento).pack(pady=10)
        
        resumo_frame = tk.Frame(frame_superior, bg=self.bg_principal)
        resumo_frame.pack(fill="x", padx=10, pady=(0, 10))
        
        self.resumo_labels = {
            'novos': tk.Label(resumo_frame, text="🆕 Novos: --", bg=self.bg_principal, 
                            fg=self.cor_novo, font=("Segoe UI", 10, "bold")),
            'desatualizados': tk.Label(resumo_frame, text="⚠️ Desatualizados: --", bg=self.bg_principal, 
                                      fg=self.cor_desatualizado, font=("Segoe UI", 10, "bold")),
            'atualizados': tk.Label(resumo_frame, text="✅ Atualizados: --", bg=self.bg_principal, 
                                   fg=self.cor_atualizado, font=("Segoe UI", 10, "bold"))
        }
        
        for label in self.resumo_labels.values():
            label.pack(side="left", padx=15)
        
        # Frame para abas com filtros
        abas_frame = tk.Frame(self, bg=self.bg_principal)
        abas_frame.pack(fill="x", padx=10, pady=(5, 0))
        
        self.filter_buttons = {}
        filtros = [
            ('todos', '📋 Todos', 'all'),
            ('novos', '🆕 Novos', 'all'),
            ('desatualizados', '⚠️ Desatualizados', 'all'),
            ('atualizados', '✅ Atualizados', 'all')
        ]
        
        for key, btn_text, _ in filtros:
            btn = tk.Button(abas_frame, text=btn_text, bg=self.bg_secundario, 
                           fg=self.fg_texto, font=("Segoe UI", 9), relief="flat", bd=0,
                           padx=15, pady=5, cursor="hand2",
                           command=lambda k=key: self._aplicar_filtro_visual(k))
            btn.pack(side="left", padx=2)
            self.filter_buttons[key] = btn
        
        # Marcar "Todos" como ativo
        self._aplicar_filtro_visual('todos')
        
        # Frame para lista com scroll
        conteudo_frame = tk.Frame(self, bg=self.bg_principal)
        conteudo_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        self._criar_lista_scroll(conteudo_frame)

    def _criar_lista_scroll(self, parent_frame):
        """Cria um widget canvas com scroll para a lista única de arquivos"""
        canvas_frame = tk.Frame(parent_frame, bg=self.bg_principal)
        canvas_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        scrollbar = ttk.Scrollbar(canvas_frame)
        scrollbar.pack(side="right", fill="y")
        
        canvas = tk.Canvas(canvas_frame, bg=self.bg_terciario, highlightthickness=0,
                          yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=canvas.yview)
        
        frame_conteudo = tk.Frame(canvas, bg=self.bg_principal)
        canvas_window = canvas.create_window((0, 0), window=frame_conteudo, anchor="nw")
        
        def atualizar_scroll_region(event=None):
            canvas.configure(scrollregion=canvas.bbox("all"))
            canvas.itemconfig(canvas_window, width=canvas.winfo_width())
        
        def ao_scroll_mouse(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
            return "break"
        
        frame_conteudo.bind("<Configure>", atualizar_scroll_region)
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(canvas_window, width=e.width))
        
        # Bind mousewheel apenas no canvas
        canvas.bind("<MouseWheel>", ao_scroll_mouse)
        frame_conteudo.bind("<MouseWheel>", ao_scroll_mouse)
        
        self._canvas = canvas
        self._frame_conteudo = frame_conteudo
        self._canvas_window = canvas_window

    def _aplicar_filtro_visual(self, filtro):
        """Aplica um filtro visual à lista e redesenha os itens visíveis"""
        self.filtro_visual = filtro
        
        # Atualizar aparência dos botões
        for key, btn in self.filter_buttons.items():
            if key == filtro:
                btn.config(bg=self.cor_atualizado, fg=self.fg_texto)
            else:
                btn.config(bg=self.bg_secundario, fg=self.fg_texto)
        
        # Reaplicar filtros de checkbox
        self._aplicar_filtros()

    def _preencher_lista_unica(self):
        """Popula a lista única com todos os arquivos"""
        if not self.resultados:
            lbl = tk.Label(self._frame_conteudo, text="ℹ️ Nenhum resultado disponível.\nExecute 'Verificar Atualizações' primeiro.", 
                          bg=self.bg_principal, fg=self.fg_texto, font=("Segoe UI", 10))
            lbl.pack(pady=20)
            return
        
        total_novos = sum(len(r['novos']) for r in self.resultados.values())
        total_desatualizados = sum(len(r['desatualizados']) for r in self.resultados.values())
        total_atualizados = sum(len(r['atualizados']) for r in self.resultados.values())

        self.resumo_labels['novos'].config(text=f"🆕 Novos: {total_novos}")
        self.resumo_labels['desatualizados'].config(text=f"⚠️ Desatualizados: {total_desatualizados}")
        self.resumo_labels['atualizados'].config(text=f"✅ Atualizados: {total_atualizados}")
        
        # Adicionar todos os arquivos com tag de tipo
        for caminho, resultado in self.resultados.items():
            # Novos
            if resultado['novos']:
                titulo_frame = tk.Frame(self._frame_conteudo, bg=self.bg_principal)
                titulo_frame.pack(fill="x", padx=10, pady=(10, 2))
                titulo_frame.tag = 'novos'
                tk.Label(titulo_frame, text=f"🆕 Novos ({len(resultado['novos'])})", bg=self.bg_principal, 
                        fg=self.cor_novo, font=("Segoe UI", 10, "bold")).pack(anchor="w")
                self.item_widgets[('titulo', 'novos', caminho)] = titulo_frame
                
                for item in resultado['novos']:
                    nome_arquivo = f"{item['nome_base']}.{item['filtro_entrada']}"
                    caminho_arquivo = item['entrada']['caminho']
                    item_frame = self._adicionar_item_arquivo(self._frame_conteudo, nome_arquivo, caminho, caminho_arquivo, item['nome_base'])
                    item_frame.tag = 'novos'
                    self.item_widgets[('item', 'novos', caminho_arquivo)] = item_frame
            
            # Desatualizados
            if resultado['desatualizados']:
                titulo_frame = tk.Frame(self._frame_conteudo, bg=self.bg_principal)
                titulo_frame.pack(fill="x", padx=10, pady=(10, 2))
                titulo_frame.tag = 'desatualizados'
                tk.Label(titulo_frame, text=f"⚠️ Desatualizados ({len(resultado['desatualizados'])})", bg=self.bg_principal, 
                        fg=self.cor_desatualizado, font=("Segoe UI", 10, "bold")).pack(anchor="w")
                self.item_widgets[('titulo', 'desatualizados', caminho)] = titulo_frame
                
                for item in resultado['desatualizados']:
                    nome_arquivo = f"{item['nome_base']} (há {item['dias']} dia(s))"
                    caminho_arquivo = item['entrada']['caminho']
                    item_frame = self._adicionar_item_arquivo(self._frame_conteudo, nome_arquivo, caminho, caminho_arquivo, item['nome_base'])
                    item_frame.tag = 'desatualizados'
                    self.item_widgets[('item', 'desatualizados', caminho_arquivo)] = item_frame
            
            # Atualizados
            if resultado['atualizados']:
                titulo_frame = tk.Frame(self._frame_conteudo, bg=self.bg_principal)
                titulo_frame.pack(fill="x", padx=10, pady=(10, 2))
                titulo_frame.tag = 'atualizados'
                tk.Label(titulo_frame, text=f"✅ Atualizados ({len(resultado['atualizados'])})", bg=self.bg_principal, 
                        fg=self.cor_atualizado, font=("Segoe UI", 10, "bold")).pack(anchor="w")
                self.item_widgets[('titulo', 'atualizados', caminho)] = titulo_frame
                
                for item in resultado['atualizados']:
                    nome_arquivo = f"{item['nome_base']}.{item['filtro_saida']}"
                    caminho_arquivo = item['saida']['caminho']
                    item_frame = self._adicionar_item_arquivo(self._frame_conteudo, nome_arquivo, caminho, caminho_arquivo, item['nome_base'])
                    item_frame.tag = 'atualizados'
                    self.item_widgets[('item', 'atualizados', caminho_arquivo)] = item_frame

    def _criar_lista_scroll(self, parent_frame):
        """Cria um widget canvas com scroll para a lista única de arquivos"""
        canvas_frame = tk.Frame(parent_frame, bg=self.bg_principal)
        canvas_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        scrollbar = ttk.Scrollbar(canvas_frame)
        scrollbar.pack(side="right", fill="y")
        
        canvas = tk.Canvas(canvas_frame, bg=self.bg_terciario, highlightthickness=0,
                          yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=canvas.yview)
        
        frame_conteudo = tk.Frame(canvas, bg=self.bg_principal)
        canvas_window = canvas.create_window((0, 0), window=frame_conteudo, anchor="nw")
        
        def atualizar_scroll_region(event=None):
            canvas.configure(scrollregion=canvas.bbox("all"))
            canvas.itemconfig(canvas_window, width=canvas.winfo_width())
        
        def ao_scroll_mouse(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
            return "break"
        
        frame_conteudo.bind("<Configure>", atualizar_scroll_region)
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(canvas_window, width=e.width))
        
        # Bind mousewheel apenas no canvas
        canvas.bind("<MouseWheel>", ao_scroll_mouse)
        frame_conteudo.bind("<MouseWheel>", ao_scroll_mouse)
        
        self._canvas = canvas
        self._frame_conteudo = frame_conteudo
        self._canvas_window = canvas_window

    def _aplicar_filtros(self):
        """Mostra/esconde itens baseado no filtro visual e checkboxes"""
        filtros = {
            'novos': self.filter_novos.get(),
            'desatualizados': self.filter_desatualizados.get(),
            'atualizados': self.filter_atualizados.get()
        }
        
        # Mostrar/esconder itens baseado nos filtros
        for (tipo_widget, tipo_arquivo, chave), widget in self.item_widgets.items():
            deve_mostrar = False
            
            # Verificar se deve mostrar baseado no filtro visual
            if self.filtro_visual == 'todos' or self.filtro_visual == tipo_arquivo:
                # Verificar se o checkbox está ativado
                if tipo_arquivo == 'novos' and filtros['novos']:
                    deve_mostrar = True
                elif tipo_arquivo == 'desatualizados' and filtros['desatualizados']:
                    deve_mostrar = True
                elif tipo_arquivo == 'atualizados' and filtros['atualizados']:
                    deve_mostrar = True
            
            if deve_mostrar:
                widget.pack(fill="x", padx=10 if tipo_widget == 'titulo' else 20, pady=2 if tipo_widget == 'item' else (10, 2))
            else:
                widget.pack_forget()

    def _propagate_scroll(self, event, widget):
        """Propaga eventos de scroll para o canvas da aba"""
        try:
            parent = widget
            while parent and not hasattr(parent, '_canvas'):
                parent = parent.master
            
            if parent and hasattr(parent, '_canvas'):
                canvas = parent._canvas
                canvas.yview_scroll(int(-1*(event.delta/120)), "units")
                return "break"
        except:
            pass

    def _adicionar_item_arquivo(self, parent_frame, nome_arquivo, caminho_pasta, caminho_arquivo, nome_base=""):
        """Adiciona um item de arquivo com dropdown desabilitado e botão de copiar caminho"""
        if not nome_base:
            nome_base = nome_arquivo.split('(')[0].strip() if '(' in nome_arquivo else nome_arquivo.split(' ')[0].strip()
        
        item_frame = tk.Frame(parent_frame, bg=self.bg_terciario)
        item_frame.pack(fill="x", padx=20, pady=2)
        
        lbl = tk.Label(item_frame, text=f"• {nome_arquivo}", bg=self.bg_terciario, 
                fg=self.fg_texto, font=("Segoe UI", 9))
        lbl.pack(side="left", padx=5, pady=3)
        
        combo = ttk.Combobox(item_frame, values=["Atualizado", "Inapto", "Ignorar"],
                            state="readonly", width=12, font=("Segoe UI", 8))
        combo.pack(side="left", padx=5, pady=3)
        
        # Restaurar valor anterior se existir
        if caminho_arquivo in self.combo_values:
            combo.set(self.combo_values[caminho_arquivo])
        
        # Salvar valor do combo quando for alterado
        def ao_mudar_combo(event=None):
            self.combo_values[caminho_arquivo] = combo.get()
        
        combo.bind("<<ComboboxSelected>>", ao_mudar_combo)
        
        # Propagação de scroll para widgets filhos
        combo.bind("<MouseWheel>", lambda e: self._propagate_scroll(e, item_frame))
        lbl.bind("<MouseWheel>", lambda e: self._propagate_scroll(e, item_frame))
        
        btn_copiar = tk.Button(item_frame, text="copiar caminho", bg=self.bg_terciario, 
                              fg="#5B8DEE", font=("Segoe UI", 9), relief="flat",
                              padx=3, pady=1, bd=0, cursor="hand2")
        btn_copiar.pack(side="left", padx=2, pady=3)
        btn_copiar.bind("<MouseWheel>", lambda e: self._propagate_scroll(e, item_frame))
        
        def ao_clicar_copiar():
            caminho_pasta_arquivo = os.path.dirname(caminho_arquivo)
            self.clipboard_clear()
            self.clipboard_append(caminho_pasta_arquivo)
            self.update()
            
            msg_label = tk.Label(item_frame, text="✅ Caminho copiado!", bg=self.bg_terciario, 
                                fg="#2ECC71", font=("Segoe UI", 9, "bold"), padx=8, pady=2)
            msg_label.pack(side="left", padx=5)
            
            def remover_msg():
                msg_label.destroy()
            
            self.after(2000, remover_msg)
        
        btn_copiar.config(command=ao_clicar_copiar)
        
        def ao_entrar_botao(event):
            btn_copiar.config(bg=self.bg_secundario)
        
        def ao_sair_botao(event):
            btn_copiar.config(bg=self.bg_terciario)
        
        btn_copiar.bind("<Enter>", ao_entrar_botao)
        btn_copiar.bind("<Leave>", ao_sair_botao)
        
        return item_frame


# ==================== INTERFACE PRINCIPAL ====================

class MonitorApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("ATLAS")
        self.geometry("500x230")
        self.resizable(False, False)
        
        self.bg_principal = "#36393F"
        self.bg_secundario = "#2F3136"
        self.bg_terciario = "#282B30"
        self.fg_texto = "#FFFFFF"
        self.fg_texto_secundario = "#B9BBBE"
        self.cor_acento = "#5865F2"
        self.cor_sucesso = "#43B581"
        self.cor_alerta = "#FAA61A"
        self.cor_erro = "#F04747"
        
        self.configure(bg=self.bg_principal)
        
        self._configurar_estilo_ttk()

        self.config = carregar_config()
        self.sessao_atual = self.config['sessao_ativa']
        self.pastas = obter_pastas_sessao(self.config, self.sessao_atual)
        self.resultados = {}

        ult = self.config.get('ultimas_extensoes', {})
        self.ultimo_entrada = ult.get('entrada', 'rvt')
        self.ultimo_saida = ult.get('saida', 'ifc')

        self.filter_novos = tk.BooleanVar(value=True)
        self.filter_desatualizados = tk.BooleanVar(value=True)
        self.filter_atualizados = tk.BooleanVar(value=True)
        
        self.visualizando_ignorados = False

        self._montar_interface()
        
        self.log_console(f"📁 Configurações salvas em: {DIRETORIO_ATLAS}")
        self.log_console(f"📄 Arquivo: {os.path.basename(CONFIG_FILE)}\n")
    
    def _configurar_estilo_ttk(self):
        """Configura o estilo visual dos widgets ttk"""
        style = ttk.Style()
        style.theme_use('clam')
        
        style.configure('TLabel', background=self.bg_principal, foreground=self.fg_texto)
        style.configure('TFrame', background=self.bg_principal)
        style.configure('TButton', background=self.bg_terciario, foreground=self.fg_texto, 
                       borderwidth=1, focuscolor='none', padding=6)
        style.map('TButton', 
                 background=[('active', self.cor_acento), ('pressed', self.cor_acento)],
                 foreground=[('active', '#ffffff'), ('pressed', '#ffffff')])
        
        style.configure('TCombobox', fieldbackground="#5865F2", background="#5865F2",
                       foreground=self.fg_texto)
        style.map('TCombobox', fieldbackground=[('readonly', '#5865F2'), ('active', '#5865F2')])
        
        style.configure('TCheckbutton', background=self.bg_principal, foreground=self.fg_texto)
        style.map('TCheckbutton', background=[('active', self.bg_principal)])

    def _montar_interface(self):
        header_frame = tk.Frame(self, bg=self.bg_secundario, height=60)
        header_frame.pack(fill="x", pady=(0, 10))
        header_frame.pack_propagate(False)
        
        ttk.Label(
            header_frame,
            text="🔄 Monitor de Atualizações de Arquivos",
            font=("Segoe UI", 16, "bold"),
            background=self.bg_secundario,
            foreground=self.cor_acento,
        ).pack(pady=12)

        frame_sessao = tk.Frame(self, bg=self.bg_principal)
        frame_sessao.pack(pady=8)
        
        ttk.Label(frame_sessao, text="Sessão Ativa:", font=("Segoe UI", 10, "bold"), background=self.bg_principal, foreground=self.fg_texto).pack(side="left", padx=5)
        
        self.combo_sessoes = ttk.Combobox(frame_sessao, width=30, state="readonly")
        self.combo_sessoes.pack(side="left", padx=5)
        self.combo_sessoes.bind("<<ComboboxSelected>>", self._trocar_sessao)
        self._atualizar_combo_sessoes()
        
        ttk.Button(frame_sessao, text="⚙️ Gerenciar Sessões", command=self._gerenciar_sessoes, width=20).pack(side="left", padx=5)
        
        frame_botoes = tk.Frame(self, bg=self.bg_principal)
        frame_botoes.pack(pady=8)

        ttk.Button(
            frame_botoes, text="📂 Adicionar Pasta(s)", width=25, command=self._adicionar_pastas
        ).grid(row=0, column=0, padx=8, pady=4)
        ttk.Button(
            frame_botoes, text="🔍 Verificar Atualizações", width=25, command=self._verificar_atualizacoes
        ).grid(row=0, column=1, padx=8, pady=4)
        ttk.Button(
            frame_botoes, text="📁 Mapeamento", width=25, command=self._gerenciar_pastas
        ).grid(row=1, column=0, padx=8, pady=4)
        ttk.Button(
            frame_botoes, text="📊 Relatório", width=25, command=self._abrir_relatorio
        ).grid(row=1, column=1, padx=8, pady=4)

    def _atualizar_combo_sessoes(self):
        """Atualiza o combobox com as sessões disponíveis"""
        sessoes = list(self.config['sessoes'].keys())
        self.combo_sessoes['values'] = sessoes
        self.combo_sessoes.set(self.sessao_atual)

    def _trocar_sessao(self, event=None):
        """Troca para a sessão selecionada"""
        nova_sessao = self.combo_sessoes.get()
        if nova_sessao == self.sessao_atual:
            return
        
        self.sessao_atual = nova_sessao
        self.config['sessao_ativa'] = nova_sessao
        salvar_config(self.config)
        
        self.carregar_sessao_ativa()
        self.log_console(f"✓ Sessão alterada para: {nova_sessao}")
        self.log_console(f"📁 Configurações salvas em: {DIRETORIO_ATLAS}\n")

    def carregar_sessao_ativa(self):
        """Carrega as pastas da sessão ativa"""
        self.pastas = obter_pastas_sessao(self.config, self.sessao_atual)
        self._atualizar_combo_sessoes()

    def _gerenciar_sessoes(self):
        """Abre janela de gerenciamento de sessões"""
        JanelaGerenciarSessoes(self, self.config, self.bg_principal, self.bg_secundario, self.fg_texto, self.fg_texto_secundario)

    def _gerenciar_pastas(self):
        """Abre janela de gerenciamento de pastas"""
        JanelaGerenciarPastas(self, self.config, self.bg_principal, self.bg_secundario, self.fg_texto, self.fg_texto_secundario)

    def _abrir_relatorio(self):
        """Abre janela de relatório"""
        JanelaRelatorio(self, self.config, self.resultados, self.bg_principal, self.bg_secundario, self.fg_texto, self.fg_texto_secundario, 
                       self.filter_novos, self.filter_desatualizados, self.filter_atualizados)

    def log_console(self, msg: str):
        """Log de mensagens no console"""
        print(msg)

    def rodar_em_thread(self, func):
        threading.Thread(target=func, daemon=True).start()

    def _ignorar_arquivos(self):
        """Permite selecionar arquivos para ignorar da pasta selecionada"""
        pass

    def _reverter_ignorados(self):
        """Remove todos os arquivos ignorados da pasta selecionada"""
        pass

    def _verificar_atualizacoes(self):
        if not self.pastas:
            messagebox.showinfo("Aviso", "Nenhuma pasta configurada nesta sessão.")
            return

        self.visualizando_ignorados = False

        dialog = tk.Toplevel(self)
        dialog.title("Verificação Concluída")
        dialog.geometry("280x160")
        dialog.resizable(False, False)
        dialog.grab_set()
        dialog.transient(self)
        dialog.configure(bg=self.bg_principal)
        
        header_frame = tk.Frame(dialog, bg=self.bg_principal)
        header_frame.pack(pady=5, padx=15)
        
        tk.Label(
            header_frame,
            text="✓ Verificação Concluída",
            font=("Segoe UI", 10, "bold"),
            background=self.bg_principal,
            foreground=self.cor_acento
        ).pack(anchor="w")
        
        info_frame = tk.Frame(dialog, bg=self.bg_principal)
        info_frame.pack(pady=(0, 5), padx=15, fill="both", expand=True)
        
        info_labels = {
            'novos': tk.Label(
                info_frame,
                text="🆕 Novos: --",
                font=("Segoe UI", 9),
                background=self.bg_principal,
                foreground=self.fg_texto
            ),
            'desatualizados': tk.Label(
                info_frame,
                text="⚠️ Desatualizados: --",
                font=("Segoe UI", 9),
                background=self.bg_principal,
                foreground=self.fg_texto
            ),
            'atualizados': tk.Label(
                info_frame,
                text="✅ Atualizados: --",
                font=("Segoe UI", 9),
                background=self.bg_principal,
                foreground=self.fg_texto
            )
        }
        
        tk.Label(
            info_frame,
            text="Resultados da Verificação:",
            font=("Segoe UI", 8),
            background=self.bg_principal,
            foreground=self.fg_texto
        ).pack(anchor="center", pady=(0, 2))
        
        for label in info_labels.values():
            label.pack(anchor="center", pady=0)
        
        button_frame = tk.Frame(dialog, bg=self.bg_principal)
        button_frame.pack(pady=5, fill="x", padx=15)
        
        buttons_inner = tk.Frame(button_frame, bg=self.bg_principal)
        buttons_inner.pack(anchor="center")
        
        def tarefa_verificacao():
            self.resultados = verificar_atualizacoes(self.pastas)
            self.resultados = self._filtrar_ignorados(self.resultados)

            total_novos = sum(len(r['novos']) for r in self.resultados.values())
            total_desatualizados = sum(len(r['desatualizados']) for r in self.resultados.values())
            total_atualizados = sum(len(r['atualizados']) for r in self.resultados.values())

            info_labels['novos'].config(text=f"🆕 Novos: {total_novos}")
            info_labels['desatualizados'].config(text=f"⚠️ Desatualizados: {total_desatualizados}")
            info_labels['atualizados'].config(text=f"✅ Atualizados: {total_atualizados}")
        
        def abrir_relatorio():
            dialog.destroy()
            self._abrir_relatorio()
        
        def atualizar():
            dialog.destroy()
            
            temp_file, command_file = set_module.gerar_temp_set(self.resultados)
            
            if not temp_file:
                messagebox.showwarning("Aviso", "Nenhum arquivo novo ou desatualizado para processar.")
                return
            
            versoes_revit = detectar_versoes_revit()
            
            if not versoes_revit:
                messagebox.showerror("Revit Não Encontrado", "Nenhuma versão de Revit foi detectada no sistema.")
                return
            
            janela_revit = JanelaSelecaoRevit(self, versoes_revit)
            self.wait_window(janela_revit)
            
            if not janela_revit.revit_selecionado:
                return
            
            nome_revit, caminho_revit = janela_revit.revit_selecionado
            
            tela = tela_carregamento(
                titulo="Carregando Revit",
                mensagem=f"Abrindo {nome_revit}...",
                duracao=60,
                parent=self
            )
            
            resultado_abertura = abrir_revit(caminho_revit)
        
        def gerar_relatorio():
            dialog.destroy()
            destino = set_module.gerar_set(self.resultados, parent=self)
            if destino:
                messagebox.showinfo("Relatório Gerado", f"Relatório salvo em:\n{destino}")
        
        ttk.Button(
            buttons_inner,
            text="Atualizar",
            command=atualizar,
            width=11
        ).pack(side="left", padx=2)
        
        ttk.Button(
            buttons_inner,
            text="Gerar set",
            command=gerar_relatorio,
            width=11
        ).pack(side="left", padx=2)
        
        ttk.Button(
            buttons_inner,
            text="Relatório",
            command=abrir_relatorio,
            width=11
        ).pack(side="left", padx=2)
        
        self.rodar_em_thread(tarefa_verificacao)
        self.wait_window(dialog)

    def _adicionar_pastas(self):
        """
        Abre a janela de seleção múltipla. Para cada pasta confirmada,
        abre o diálogo de escolha de extensões usando como padrão as
        últimas escolhas (persistidas em config). 
        """
        janela = JanelaSelecaoPastas(self)
        self.wait_window(janela)

        if not getattr(janela, 'pastas_selecionadas', None):
            return

        for caminho in janela.pastas_selecionadas:
            existe = any(p['caminho'] == caminho for p in self.pastas)
            if existe:
                self.log_console(f"⚠️ Pasta já configurada, pulando: {caminho}")
                continue

            self._configurar_extensoes_pasta(caminho)

    def _configurar_extensoes_pasta(self, caminho):
        entrada_win = tk.Toplevel(self)
        entrada_win.title("Escolher Extensões")
        entrada_win.geometry("420x400")
        entrada_win.resizable(False, False)
        entrada_win.grab_set()
        entrada_win.transient(self)
        entrada_win.configure(bg="#f0f0f0")

        confirmado = [False]

        main_frame = ttk.Frame(entrada_win, padding="20 15 20 20")
        main_frame.pack(fill="both", expand=True)

        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill="x", pady=(0, 15))

        ttk.Label(
            header_frame,
            text="📁 Configurar Extensões",
            font=("Segoe UI", 14, "bold"),
        ).pack(anchor="w")

        ttk.Separator(main_frame).pack(fill="x", pady=(0, 15))

        info_frame = ttk.Frame(main_frame)
        info_frame.pack(fill="x", pady=(0, 15))

        ttk.Label(
            info_frame,
            text="Pasta Selecionada:",
            font=("Segoe UI", 10, "bold"),
        ).pack(anchor="w")

        ttk.Label(
            info_frame,
            text=os.path.basename(caminho),
            font=("Segoe UI", 11),
            foreground="#1a73e8",
        ).pack(anchor="w", pady=(2, 5))

        ttk.Label(
            info_frame,
            text="Caminho completo:",
            font=("Segoe UI", 9),
        ).pack(anchor="w")

        caminho_label = ttk.Label(
            info_frame,
            text=caminho,
            font=("Segoe UI", 9),
            foreground="#666666",
            wraplength=380
        )
        caminho_label.pack(anchor="w", pady=(0, 10))

        ext_frame = ttk.Frame(main_frame)
        ext_frame.pack(fill="x", pady=(0, 20))

        entrada_frame = ttk.Frame(ext_frame)
        entrada_frame.pack(fill="x", pady=(0, 15))

        ttk.Label(
            entrada_frame,
            text="Extensão de Entrada:",
            font=("Segoe UI", 10),
        ).pack(anchor="w", pady=(0, 5))

        default_entrada = self.config.get('ultimas_extensoes', {}).get('entrada', self.ultimo_entrada)
        entrada_var = tk.StringVar(value=default_entrada)
        entrada_combo = ttk.Combobox(
            entrada_frame,
            textvariable=entrada_var,
            values=["dwg", "rvt", "rfa"],
            state="readonly",
            width=25
        )
        entrada_combo.pack(anchor="w")

        saida_frame = ttk.Frame(ext_frame)
        saida_frame.pack(fill="x")

        ttk.Label(
            saida_frame,
            text="Extensão de Saída:",
            font=("Segoe UI", 10),
        ).pack(anchor="w", pady=(0, 10))

        default_saida = self.config.get('ultimas_extensoes', {}).get('saida', self.ultimo_saida)
        saida_var = tk.StringVar(value=default_saida)
        saida_combo = ttk.Combobox(
            saida_frame,
            textvariable=saida_var,
            values=["ifc", "nwc"],
            state="readonly",
            width=25
        )
        saida_combo.pack(anchor="w")

        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill="x", pady=(10, 0))

        ttk.Button(
            button_frame,
            text="Cancelar",
            command=entrada_win.destroy,
            style="Secondary.TButton",
            width=15
        ).pack(side="right", padx=(5, 0))

        def confirmar():
            self.pastas.append({
                "caminho": caminho,
                "entrada": entrada_var.get(),
                "saida": saida_var.get()
            })
            self.ultimo_entrada = entrada_var.get()
            self.ultimo_saida = saida_var.get()
            self.config['ultimas_extensoes'] = {
                'entrada': self.ultimo_entrada,
                'saida': self.ultimo_saida
            }
            atualizar_pastas_sessao(self.config, self.sessao_atual, self.pastas)
            salvar_config(self.config)
            self.log_console(f"📂 Pasta adicionada: {caminho} ({entrada_var.get()} → {saida_var.get()})")
            confirmado[0] = True
            entrada_win.destroy()

        ttk.Button(
            button_frame,
            text="✓ Confirmar",
            command=confirmar,
            style="Primary.TButton",
            width=15
        ).pack(side="right", padx=(0, 5))

        style = ttk.Style()
        style.configure("Primary.TButton", background="#007bff", foreground="black")
        style.configure("Secondary.TButton", background="#6c757d")

        entrada_win.update_idletasks()
        width = entrada_win.winfo_width()
        height = entrada_win.winfo_height()
        x = (entrada_win.winfo_screenwidth() // 2) - (width // 2)
        y = (entrada_win.winfo_screenheight() // 2) - (height // 2)
        entrada_win.geometry(f"{width}x{height}+{x}+{y}")

        self.wait_window(entrada_win)
        return confirmado[0]

    def _filtrar_ignorados(self, resultados):
        """Filtra resultados removendo arquivos ignorados"""
        if 'arquivos_ignorados' not in self.config:
            return resultados
        
        resultados_filtrados = {}
        for caminho_pasta, resultado in resultados.items():
            ignorados = set(self.config['arquivos_ignorados'].get(caminho_pasta, []))
            
            novos = [r for r in resultado['novos'] if not self._arquivo_esta_ignorado(r, ignorados)]
            desatualizados = [r for r in resultado['desatualizados'] if not self._arquivo_esta_ignorado(r, ignorados)]
            atualizados = [r for r in resultado['atualizados'] if not self._arquivo_esta_ignorado(r, ignorados)]
            
            resultados_filtrados[caminho_pasta] = {
                'config': resultado['config'],
                'novos': novos,
                'desatualizados': desatualizados,
                'atualizados': atualizados,
                'total_entrada': resultado['total_entrada'],
                'total_saida': resultado['total_saida']
            }
        
        return resultados_filtrados

    def _arquivo_esta_ignorado(self, arquivo_info, ignorados):
        """Verifica se um arquivo está na lista de ignorados"""
        nome_base = arquivo_info.get('nome_base', '')
        
        if nome_base in ignorados:
            return True
        
        info_entrada = arquivo_info.get('entrada', {})
        if info_entrada:
            arquivo_entrada = info_entrada.get('arquivo', '')
            if arquivo_entrada in ignorados:
                return True
        
        nome_sem_ext = nome_base.rsplit('.', 1)[0] if '.' in nome_base else nome_base
        for ignorado in ignorados:
            ignorado_sem_ext = ignorado.rsplit('.', 1)[0] if '.' in ignorado else ignorado
            if nome_sem_ext == ignorado_sem_ext:
                return True
        
        return False


if __name__ == "__main__":
    app = MonitorApp()
    app.mainloop()
