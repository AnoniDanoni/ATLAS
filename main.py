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


# ==================== JANELA DE RELATÓRIO DE ARQUIVO INAPTO ====================

class JanelaRelatorioArquivo(tk.Toplevel):
    """Janela para criar/editar relatório de arquivo inapto"""
    
    def __init__(self, parent, nome_arquivo, caminho_arquivo, config, bg_principal, bg_secundario, fg_texto, fg_texto_secundario, btn_relatorio=None, combo=None):
        super().__init__(parent)
        self.title(f"📝 Relatório - {nome_arquivo}")
        self.geometry("600x500")
        self.configure(bg=bg_principal)
        self.grab_set()
        self.transient(parent)
        
        self.nome_arquivo = nome_arquivo
        self.caminho_arquivo = caminho_arquivo
        self.config = config
        self.btn_relatorio = btn_relatorio
        self.combo = combo
        self.foi_salvo = False
        self.bg_principal = bg_principal
        self.bg_secundario = bg_secundario
        self.bg_terciario = "#282B30"
        self.fg_texto = fg_texto
        self.fg_texto_secundario = fg_texto_secundario
        self.cor_acento = "#5865F2"
        
        # Inicializar estrutura de relatórios se não existir
        if 'relatorios_inaptid' not in self.config:
            self.config['relatorios_inaptid'] = {}
        
        # Capturar evento de fechamento
        self.protocol("WM_DELETE_WINDOW", self._ao_fechar)
        
        self._montar_interface()
        self._carregar_relatorio()
        
    def _montar_interface(self):
        """Monta a interface da janela"""
        # Header
        header_frame = tk.Frame(self, bg=self.bg_secundario)
        header_frame.pack(fill="x", pady=(0, 10))
        
        ttk.Label(header_frame, text=f"📝 Relatório de Arquivo Inapto", 
                 font=("Segoe UI", 11, "bold"), background=self.bg_secundario, 
                 foreground=self.cor_acento).pack(pady=10)
        
        # Info do arquivo
        info_frame = tk.Frame(self, bg=self.bg_principal)
        info_frame.pack(fill="x", padx=15, pady=(0, 10))
        
        ttk.Label(info_frame, text=f"Arquivo: {self.nome_arquivo}", 
                 font=("Segoe UI", 9), background=self.bg_principal, 
                 foreground=self.fg_texto).pack(anchor="w")
        
        ttk.Label(info_frame, text=f"Caminho: {self.caminho_arquivo}", 
                 font=("Segoe UI", 8), background=self.bg_principal, 
                 foreground=self.fg_texto_secundario).pack(anchor="w", pady=(3, 0))
        
        # Texto do relatório
        ttk.Label(self, text="Motivo da inaptidão:", 
                 font=("Segoe UI", 10, "bold"), background=self.bg_principal, 
                 foreground=self.fg_texto).pack(anchor="w", padx=15, pady=(0, 3))
        
        frame_texto = tk.Frame(self, bg=self.cor_acento, height=200)
        frame_texto.pack(fill="x", padx=15, pady=(0, 10))
        frame_texto.pack_propagate(False)
        
        frame_texto_inner = tk.Frame(frame_texto, bg=self.bg_principal)
        frame_texto_inner.pack(fill="both", expand=True, padx=2, pady=2)
        
        scrollbar = ttk.Scrollbar(frame_texto_inner)
        scrollbar.pack(side="right", fill="y")
        
        self.texto_relatorio = tk.Text(frame_texto_inner, 
                                       bg=self.bg_terciario, 
                                       fg=self.fg_texto,
                                       font=("Segoe UI", 9),
                                       height=8,
                                       relief="flat",
                                       borderwidth=0,
                                       yscrollcommand=scrollbar.set,
                                       wrap="word",
                                       padx=8,
                                       pady=8)
        self.texto_relatorio.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=self.texto_relatorio.yview)
        
        # Botões
        btn_frame = tk.Frame(self, bg=self.bg_principal)
        btn_frame.pack(fill="x", padx=15, pady=10)
        
        ttk.Button(btn_frame, text="Cancelar", command=self._ao_fechar, width=20).pack(side="right", padx=(5, 0))
        ttk.Button(btn_frame, text="✓ OK", command=self._salvar, width=20).pack(side="right")

    
    def _carregar_relatorio(self):
        """Carrega o relatório salvo se existir"""
        if self.caminho_arquivo in self.config['relatorios_inaptid']:
            relatorio = self.config['relatorios_inaptid'][self.caminho_arquivo]
            self.texto_relatorio.insert("1.0", relatorio)
    
    def _ao_fechar(self):
        """Handler para fechar a janela (sem salvar)"""
        if not self.foi_salvo:
            # Se não foi salvo e existe um combo, restaurar para "Status"
            if self.combo:
                self.combo.set("Status")
                # Limpar o status salvo também
                if 'status_arquivos' in self.config and self.caminho_arquivo in self.config['status_arquivos']:
                    del self.config['status_arquivos'][self.caminho_arquivo]
                    salvar_config(self.config)
        
        self.destroy()
    
    def _salvar(self):
        """Salva o relatório"""
        texto = self.texto_relatorio.get("1.0", "end-1c")
        
        if not texto.strip():
            messagebox.showwarning("Aviso", "Digite o motivo da inaptidão!")
            return
        
        if 'relatorios_inaptid' not in self.config:
            self.config['relatorios_inaptid'] = {}
        
        self.config['relatorios_inaptid'][self.caminho_arquivo] = texto

        salvar_config(self.config)
        
        # Mostrar o botão de relatório se foi passado
        if self.btn_relatorio and not self.btn_relatorio.winfo_ismapped():
            self.btn_relatorio.pack(side="left", padx=2, pady=3)
        
        self.foi_salvo = True
        messagebox.showinfo("Sucesso", "Relatório salvo com sucesso!")
        self.destroy()


# ==================== JANELA DE RELATÓRIO ====================

class JanelaRelatorio(tk.Toplevel):
    def __init__(self, parent, config, resultados, bg_principal, bg_secundario, fg_texto, fg_texto_secundario, 
                 filter_novos, filter_desatualizados, filter_atualizados):
        super().__init__(parent)
        self.title("📊 Relatório")
        self.geometry("1000x700")
        self.configure(bg=bg_principal)
        self.resizable(True, True)
        self.attributes('-topmost', True)
        self.after_idle(self.attributes, '-topmost', False)
        
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
        
        self._montar_interface()
        self._aplicar_filtros()
        
        # Recarregar config quando a janela fechar para sincronizar mudanças
        self.protocol("WM_DELETE_WINDOW", self._ao_fechar)
        
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
        
        header_frame = tk.Frame(frame_superior, bg=self.bg_secundario)
        header_frame.pack(fill="x", padx=10, pady=(10, 5))
        
        ttk.Label(header_frame, text="📊 Relatório de Atualizações", 
                 font=("Segoe UI", 12, "bold"), background=self.bg_secundario, 
                 foreground=self.cor_acento).pack(side="left", pady=10)
        
        btn_exportar = ttk.Button(header_frame, text="📥 Exportar CSV", command=self._exportar_csv)
        btn_exportar.pack(side="right", padx=10)
        
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
        
        conteudo_frame = tk.Frame(self, bg=self.bg_principal)
        conteudo_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        self.notebook = ttk.Notebook(conteudo_frame)
        self.notebook.pack(fill="both", expand=True)
        
        self.tab_todos = tk.Frame(self.notebook, bg=self.bg_principal)
        self.tab_novos = tk.Frame(self.notebook, bg=self.bg_principal)
        self.tab_desatualizados = tk.Frame(self.notebook, bg=self.bg_principal)
        self.tab_atualizados = tk.Frame(self.notebook, bg=self.bg_principal)
        
        self.notebook.add(self.tab_todos, text="📋 Todos")
        self.notebook.add(self.tab_novos, text="🆕 Novos")
        self.notebook.add(self.tab_desatualizados, text="⚠️ Desatualizados")
        self.notebook.add(self.tab_atualizados, text="✅ Atualizados")
        
        self._criar_aba_scroll(self.tab_todos)
        self._criar_aba_scroll(self.tab_novos)
        self._criar_aba_scroll(self.tab_desatualizados)
        self._criar_aba_scroll(self.tab_atualizados)

    def _criar_aba_scroll(self, tab_frame):
        """Cria um widget canvas com scroll para uma aba com controles por arquivo"""
        canvas_frame = tk.Frame(tab_frame, bg=self.bg_principal)
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
        
        def _bind_mousewheel(widget):
            """Bind mousewheel recursivamente em todos os widgets"""
            widget.bind("<MouseWheel>", ao_scroll_mouse, add="+")
            for child in widget.winfo_children():
                _bind_mousewheel(child)
        
        frame_conteudo.bind("<Configure>", atualizar_scroll_region)
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(canvas_window, width=e.width))
        
        # Bind mousewheel em todo o frame
        _bind_mousewheel(frame_conteudo)
        canvas.bind("<MouseWheel>", ao_scroll_mouse, add="+")
        tab_frame.bind("<MouseWheel>", ao_scroll_mouse, add="+")
        
        tab_frame._canvas = canvas
        tab_frame._frame_conteudo = frame_conteudo
        tab_frame._canvas_window = canvas_window
        tab_frame._bind_mousewheel = _bind_mousewheel

    def _criar_label_selecionavel(self, parent, texto, bg, fg, font_spec, padx=5, pady=3):
        """Cria um widget de texto selecionável sem bordas, estilizado como label"""
        text_widget = tk.Text(parent, height=1, width=max(20, len(texto)), bg=bg, fg=fg,
                             font=font_spec, relief="flat", borderwidth=0,
                             cursor="arrow", wrap="none", insertwidth=0)
        text_widget.insert("1.0", texto)
        text_widget.config(state="disabled")
        text_widget.pack(side="left", padx=padx, pady=pady)
        
        # O widget Text com state="disabled" permite seleção de texto e Ctrl+C automaticamente
        
        return text_widget

    def _aplicar_filtros(self):
        """Aplica filtros e atualiza o relatório"""
        filtros = {
            'novos': self.filter_novos.get(),
            'desatualizados': self.filter_desatualizados.get(),
            'atualizados': self.filter_atualizados.get()
        }
        
        if not self.resultados:
            for widget in self.tab_todos._frame_conteudo.winfo_children():
                widget.destroy()
            lbl = tk.Label(self.tab_todos._frame_conteudo, text="ℹ️ Nenhum resultado disponível.\nExecute 'Verificar Atualizações' primeiro.", 
                          bg=self.bg_principal, fg=self.fg_texto, font=("Segoe UI", 10))
            lbl.pack(pady=20)
            return

        total_novos = sum(len(r['novos']) for r in self.resultados.values())
        total_desatualizados = sum(len(r['desatualizados']) for r in self.resultados.values())
        total_atualizados = sum(len(r['atualizados']) for r in self.resultados.values())

        self.resumo_labels['novos'].config(text=f"🆕 Novos: {total_novos}")
        self.resumo_labels['desatualizados'].config(text=f"⚠️ Desatualizados: {total_desatualizados}")
        self.resumo_labels['atualizados'].config(text=f"✅ Atualizados: {total_atualizados}")

        self._preencher_aba_todos(filtros)
        self._preencher_aba_novos(filtros)
        self._preencher_aba_desatualizados(filtros)
        self._preencher_aba_atualizados(filtros)

        for tab in (self.tab_todos, self.tab_novos, self.tab_desatualizados, self.tab_atualizados):
            tab._bind_mousewheel(tab._frame_conteudo)

    def _preencher_aba_todos(self, filtros):
        """Preenche a aba de todos os resultados com dropdown para cada arquivo"""
        for widget in self.tab_todos._frame_conteudo.winfo_children():
            widget.destroy()
        
        total_novos = sum(len(r['novos']) for r in self.resultados.values())
        total_desatualizados = sum(len(r['desatualizados']) for r in self.resultados.values())
        total_atualizados = sum(len(r['atualizados']) for r in self.resultados.values())
        
        if total_novos == 0 and total_desatualizados == 0 and total_atualizados == 0:
            lbl = tk.Label(self.tab_todos._frame_conteudo, 
                          text="ℹ️ Nenhum resultado disponível.\nExecute 'Verificar Atualizações' primeiro.", 
                          bg=self.bg_principal, fg=self.fg_texto, font=("Segoe UI", 10))
            lbl.pack(pady=20)
            return
        
        if filtros['novos'] and total_novos > 0:
            titulo_frame = tk.Frame(self.tab_todos._frame_conteudo, bg=self.bg_principal)
            titulo_frame.pack(fill="x", padx=10, pady=(10, 2))
            tk.Label(titulo_frame, text=f"🆕 Novos ({total_novos})", bg=self.bg_principal, 
                    fg=self.cor_novo, font=("Segoe UI", 10, "bold")).pack(anchor="w")
            
            for caminho, resultado in sorted(self.resultados.items(), key=lambda x: x[0].lower()):
                novos = resultado['novos']
                if not novos:
                    continue
                
                pasta_frame = tk.Frame(self.tab_todos._frame_conteudo, bg=self.bg_principal)
                pasta_frame.pack(fill="x", padx=10, pady=(5, 2))
                self._criar_label_selecionavel(pasta_frame, f"📁 {caminho}", bg=self.bg_principal, 
                        fg=self.fg_texto, font_spec=("Segoe UI", 9, "bold"))
                
                for item in novos:
                    nome_arquivo = f"{item['nome_base']}.{item['filtro_entrada']}"
                    caminho_arquivo = item['entrada']['caminho']
                    nome_base = item['nome_base']
                    self._adicionar_item_arquivo(self.tab_todos._frame_conteudo, nome_arquivo, caminho, caminho_arquivo, nome_base)
        
        if filtros['desatualizados'] and total_desatualizados > 0:
            titulo_frame = tk.Frame(self.tab_todos._frame_conteudo, bg=self.bg_principal)
            titulo_frame.pack(fill="x", padx=10, pady=(10, 2))
            tk.Label(titulo_frame, text=f"⚠️ Desatualizados ({total_desatualizados})", bg=self.bg_principal, 
                    fg=self.cor_desatualizado, font=("Segoe UI", 10, "bold")).pack(anchor="w")
            
            for caminho, resultado in sorted(self.resultados.items(), key=lambda x: x[0].lower()):
                desatualizados = resultado['desatualizados']
                if not desatualizados:
                    continue
                
                pasta_frame = tk.Frame(self.tab_todos._frame_conteudo, bg=self.bg_principal)
                pasta_frame.pack(fill="x", padx=10, pady=(5, 2))
                self._criar_label_selecionavel(pasta_frame, f"📁 {caminho}", bg=self.bg_principal, 
                        fg=self.fg_texto, font_spec=("Segoe UI", 9, "bold"))
                
                for item in desatualizados:
                    nome_arquivo = f"{item['nome_base']} (há {item['dias']} dia(s))"
                    caminho_arquivo = item['entrada']['caminho']
                    nome_base = item['nome_base']
                    self._adicionar_item_arquivo(self.tab_todos._frame_conteudo, nome_arquivo, caminho, caminho_arquivo, nome_base)
        
        if filtros['atualizados'] and total_atualizados > 0:
            titulo_frame = tk.Frame(self.tab_todos._frame_conteudo, bg=self.bg_principal)
            titulo_frame.pack(fill="x", padx=10, pady=(10, 2))
            tk.Label(titulo_frame, text=f"✅ Atualizados ({total_atualizados})", bg=self.bg_principal, 
                    fg=self.cor_atualizado, font=("Segoe UI", 10, "bold")).pack(anchor="w")
            
            for caminho, resultado in sorted(self.resultados.items(), key=lambda x: x[0].lower()):
                atualizados = resultado['atualizados']
                if not atualizados:
                    continue
                
                pasta_frame = tk.Frame(self.tab_todos._frame_conteudo, bg=self.bg_principal)
                pasta_frame.pack(fill="x", padx=10, pady=(5, 2))
                self._criar_label_selecionavel(pasta_frame, f"📁 {caminho}", bg=self.bg_principal, 
                        fg=self.fg_texto, font_spec=("Segoe UI", 9, "bold"))
                
                for item in atualizados:
                    nome_arquivo = item['nome_base']
                    caminho_arquivo = item['entrada']['caminho']
                    nome_base = item['nome_base']
                    self._adicionar_item_arquivo(self.tab_todos._frame_conteudo, nome_arquivo, caminho, caminho_arquivo, nome_base)

    def _preencher_aba_novos(self, filtros):
        """Preenche a aba de novos con dropdown para cada arquivo"""
        for widget in self.tab_novos._frame_conteudo.winfo_children():
            widget.destroy()
        
        if not filtros['novos']:
            lbl = tk.Label(self.tab_novos._frame_conteudo, text="Filtro desativado", 
                          bg=self.bg_principal, fg=self.fg_texto, font=("Segoe UI", 9))
            lbl.pack(pady=20)
            return
        
        total_novos = sum(len(r['novos']) for r in self.resultados.values())
        
        if total_novos == 0:
            lbl = tk.Label(self.tab_novos._frame_conteudo, 
                          text="✅ Nenhum arquivo novo\n(Todos os arquivos já foram exportados)", 
                          bg=self.bg_principal, fg=self.fg_texto, font=("Segoe UI", 10))
            lbl.pack(pady=20)
            return
        
        titulo_frame = tk.Frame(self.tab_novos._frame_conteudo, bg=self.bg_principal)
        titulo_frame.pack(fill="x", padx=10, pady=(10, 5))
        tk.Label(titulo_frame, text=f"📊 Total: {total_novos} arquivo(s) novo(s)", 
                bg=self.bg_principal, fg=self.cor_novo, font=("Segoe UI", 10, "bold")).pack(anchor="w")
        
        for caminho, resultado in sorted(self.resultados.items(), key=lambda x: x[0].lower()):
            novos = resultado['novos']
            if not novos:
                continue
            
            pasta_frame = tk.Frame(self.tab_novos._frame_conteudo, bg=self.bg_principal)
            pasta_frame.pack(fill="x", padx=10, pady=(10, 2))
            self._criar_label_selecionavel(pasta_frame, f"📁 {caminho}", bg=self.bg_principal, 
                    fg=self.cor_acento, font_spec=("Segoe UI", 9, "bold"))
            
            config_frame = tk.Frame(self.tab_novos._frame_conteudo, bg=self.bg_principal)
            config_frame.pack(fill="x", padx=20, pady=(0, 5))
            tk.Label(config_frame, text=f"Filtro: {resultado['config']['entrada'].upper()} → {resultado['config']['saida'].upper()}", 
                    bg=self.bg_principal, fg=self.fg_texto_secundario, font=("Segoe UI", 8)).pack(anchor="w")
            
            for item in novos:
                nome_arquivo = f"{item['nome_base']}.{item['filtro_entrada']}"
                caminho_arquivo = item['entrada']['caminho']
                nome_base = item['nome_base']
                self._adicionar_item_arquivo(self.tab_novos._frame_conteudo, nome_arquivo, caminho, caminho_arquivo, nome_base)

    def _adicionar_item_arquivo(self, parent_frame, nome_arquivo, caminho_pasta, caminho_arquivo, nome_base=""):
        """Adiciona um item de arquivo com dropdown desabilitado e botão de copiar caminho"""
        if not nome_base:
            nome_base = nome_arquivo.split('(')[0].strip() if '(' in nome_arquivo else nome_arquivo.split(' ')[0].strip()
        
        item_frame = tk.Frame(parent_frame, bg=self.bg_terciario)
        item_frame.pack(fill="x", padx=20, pady=2)
        
        self._criar_label_selecionavel(item_frame, f"• {nome_arquivo}", 
                                        bg=self.bg_terciario, fg=self.fg_texto,
                                        font_spec=("Segoe UI", 9))
        
        combo = ttk.Combobox(item_frame, values=["Atualizado", "Inapto", "Ignorar"],
                            state="readonly", width=12, font=("Segoe UI", 8))
        
        # Carregar status anterior se existir
        if 'status_arquivos' in self.config and caminho_arquivo in self.config['status_arquivos']:
            status_anterior = self.config['status_arquivos'][caminho_arquivo]
            combo.set(status_anterior)
        else:
            combo.set("Status")
        
        combo.pack(side="left", padx=5, pady=3)
        
        btn_copiar = tk.Button(item_frame, text="copiar caminho", bg=self.bg_terciario, 
                              fg="#5B8DEE", font=("Segoe UI", 9), relief="flat",
                              padx=3, pady=1, bd=0, cursor="hand2")
        btn_copiar.pack(side="left", padx=2, pady=3)
        
        # Botão para abrir relatório (inicialmente oculto)
        btn_relatorio = tk.Button(item_frame, text="abrir relatório", bg=self.bg_terciario, 
                                 fg="#2ECC71", font=("Segoe UI", 9), relief="flat",
                                 padx=3, pady=1, bd=0, cursor="hand2")
        # Só mostrar se existe relatório salvo E o status é "Inapto"
        if ('relatorios_inaptid' in self.config and caminho_arquivo in self.config['relatorios_inaptid'] and 
            'status_arquivos' in self.config and self.config['status_arquivos'].get(caminho_arquivo) == 'Inapto'):
            btn_relatorio.pack(side="left", padx=2, pady=3)
        
        def ao_mudar_status(event=None):
            """Callback quando o status é alterado"""
            status_selecionado = combo.get()
            
            if status_selecionado == "Ignorar":
                # Pedir confirmação para ignorar
                if not messagebox.askyesno("Confirmar", f"Deseja ignorar este arquivo?\n\n{nome_arquivo}\n\nEle será adicionado à lista de ignorados."):
                    # Resetar o combo se o usuário cancelar
                    if 'status_arquivos' in self.config and caminho_arquivo in self.config['status_arquivos']:
                        combo.set(self.config['status_arquivos'][caminho_arquivo])
                    else:
                        combo.set("Status")
                    return
                
                # Adicionar às ignorados da pasta mapeada
                if 'arquivos_ignorados' not in self.config:
                    self.config['arquivos_ignorados'] = {}
                if caminho_pasta not in self.config['arquivos_ignorados']:
                    self.config['arquivos_ignorados'][caminho_pasta] = []
                
                # Adicionar o nome base se não estiver já
                if nome_base not in self.config['arquivos_ignorados'][caminho_pasta]:
                    self.config['arquivos_ignorados'][caminho_pasta].append(nome_base)
                
                # Remover do status_arquivos se existir
                if 'status_arquivos' in self.config and caminho_arquivo in self.config['status_arquivos']:
                    del self.config['status_arquivos'][caminho_arquivo]
                
                salvar_config(self.config)
                messagebox.showinfo("Sucesso", f"✓ Arquivo '{nome_arquivo}' adicionado à lista de ignorados!")
                # Limpar o item da interface atualizando
                item_frame.pack_forget()
                return
            
            # Pegar status anterior ANTES de salvar o novo
            status_anterior = self.config.get('status_arquivos', {}).get(caminho_arquivo)
            
            # Salvar o status
            if 'status_arquivos' not in self.config:
                self.config['status_arquivos'] = {}
            self.config['status_arquivos'][caminho_arquivo] = status_selecionado
            salvar_config(self.config)
            
            if status_selecionado == "Inapto":
                # Se estava em outro status, limpar o relatório anterior
                if status_anterior and status_anterior != "Inapto" and caminho_arquivo in self.config.get('relatorios_inaptid', {}):
                    # Remover relatório anterior
                    del self.config['relatorios_inaptid'][caminho_arquivo]
                    salvar_config(self.config)
                
                # Mostrar o botão de relatório como opcional
                if btn_relatorio.winfo_ismapped() == 0:  # Se não está visível
                    btn_relatorio.pack(side="left", padx=2, pady=3)
            else:
                # Se mudou de Inapto para outra coisa, esconder o botão de relatório
                if btn_relatorio.winfo_ismapped():
                    btn_relatorio.pack_forget()
        
        combo.bind("<<ComboboxSelected>>", ao_mudar_status)
        
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
        
        def ao_clicar_relatorio():
            """Abre o relatório para edição"""
            JanelaRelatorioArquivo(self, nome_arquivo, caminho_arquivo, self.config, 
                                 self.bg_principal, self.bg_secundario, self.fg_texto, 
                                 self.fg_texto_secundario, btn_relatorio, combo)
        
        btn_copiar.config(command=ao_clicar_copiar)
        btn_relatorio.config(command=ao_clicar_relatorio)
        
        def ao_entrar_copiar(event):
            btn_copiar.config(bg=self.bg_secundario)
        
        def ao_sair_copiar(event):
            btn_copiar.config(bg=self.bg_terciario)
        
        def ao_entrar_relatorio(event):
            btn_relatorio.config(bg=self.bg_secundario)
        
        def ao_sair_relatorio(event):
            btn_relatorio.config(bg=self.bg_terciario)
        
        btn_copiar.bind("<Enter>", ao_entrar_copiar)
        btn_copiar.bind("<Leave>", ao_sair_copiar)
        btn_relatorio.bind("<Enter>", ao_entrar_relatorio)
        btn_relatorio.bind("<Leave>", ao_sair_relatorio)


    def _remover_arquivo_ignorado(self, nome_base, caminho_pasta):
        """Remove o arquivo ignorado dos resultados"""
        if caminho_pasta not in self.resultados:
            return
        
        resultado = self.resultados[caminho_pasta]
        
        self.resultados[caminho_pasta]['novos'] = [
            r for r in resultado['novos'] 
            if r.get('nome_base', '') != nome_base
        ]
        
        self.resultados[caminho_pasta]['desatualizados'] = [
            r for r in resultado['desatualizados'] 
            if r.get('nome_base', '') != nome_base
        ]
        
        self.resultados[caminho_pasta]['atualizados'] = [
            r for r in resultado['atualizados'] 
            if r.get('nome_base', '') != nome_base
        ]

    def _preencher_aba_desatualizados(self, filtros):
        """Preenche a aba de desatualizados com dropdown para cada arquivo"""
        for widget in self.tab_desatualizados._frame_conteudo.winfo_children():
            widget.destroy()
        
        if not filtros['desatualizados']:
            lbl = tk.Label(self.tab_desatualizados._frame_conteudo, text="Filtro desativado", 
                          bg=self.bg_principal, fg=self.fg_texto, font=("Segoe UI", 9))
            lbl.pack(pady=20)
            return
        
        total_desatualizados = sum(len(r['desatualizados']) for r in self.resultados.values())
        
        if total_desatualizados == 0:
            lbl = tk.Label(self.tab_desatualizados._frame_conteudo, 
                          text="✅ Nenhum arquivo desatualizado\n(Tudo está sincronizado)", 
                          bg=self.bg_principal, fg=self.fg_texto, font=("Segoe UI", 10))
            lbl.pack(pady=20)
            return
        
        titulo_frame = tk.Frame(self.tab_desatualizados._frame_conteudo, bg=self.bg_principal)
        titulo_frame.pack(fill="x", padx=10, pady=(10, 5))
        tk.Label(titulo_frame, text=f"📊 Total: {total_desatualizados} arquivo(s) desatualizado(s)", 
                bg=self.bg_principal, fg=self.cor_desatualizado, font=("Segoe UI", 10, "bold")).pack(anchor="w")
        
        for caminho, resultado in sorted(self.resultados.items(), key=lambda x: x[0].lower()):
            desatualizados = resultado['desatualizados']
            if not desatualizados:
                continue
            
            pasta_frame = tk.Frame(self.tab_desatualizados._frame_conteudo, bg=self.bg_principal)
            pasta_frame.pack(fill="x", padx=10, pady=(10, 2))
            self._criar_label_selecionavel(pasta_frame, f"📁 {caminho}", bg=self.bg_principal, 
                    fg=self.cor_acento, font_spec=("Segoe UI", 9, "bold"))
            
            config_frame = tk.Frame(self.tab_desatualizados._frame_conteudo, bg=self.bg_principal)
            config_frame.pack(fill="x", padx=20, pady=(0, 5))
            tk.Label(config_frame, text=f"Filtro: {resultado['config']['entrada'].upper()} → {resultado['config']['saida'].upper()}", 
                    bg=self.bg_principal, fg=self.fg_texto_secundario, font=("Segoe UI", 8)).pack(anchor="w")
            
            for item in desatualizados:
                nome_arquivo = f"{item['nome_base']} (há {item['dias']} dia(s))"
                caminho_arquivo = item['entrada']['caminho']
                nome_base = item['nome_base']
                self._adicionar_item_arquivo(self.tab_desatualizados._frame_conteudo, nome_arquivo, caminho, caminho_arquivo, nome_base)

    def _preencher_aba_atualizados(self, filtros):
        """Preenche a aba de atualizados com dropdown para cada arquivo"""
        for widget in self.tab_atualizados._frame_conteudo.winfo_children():
            widget.destroy()
        
        if not filtros['atualizados']:
            lbl = tk.Label(self.tab_atualizados._frame_conteudo, text="Filtro desativado", 
                          bg=self.bg_principal, fg=self.fg_texto, font=("Segoe UI", 9))
            lbl.pack(pady=20)
            return
        
        total_atualizados = sum(len(r['atualizados']) for r in self.resultados.values())
        
        if total_atualizados == 0:
            lbl = tk.Label(self.tab_atualizados._frame_conteudo, 
                          text="ℹ️ Nenhum arquivo atualizado\n(Execute a verificação para ver resultados)", 
                          bg=self.bg_principal, fg=self.fg_texto, font=("Segoe UI", 10))
            lbl.pack(pady=20)
            return
        
        titulo_frame = tk.Frame(self.tab_atualizados._frame_conteudo, bg=self.bg_principal)
        titulo_frame.pack(fill="x", padx=10, pady=(10, 5))
        tk.Label(titulo_frame, text=f"📊 Total: {total_atualizados} arquivo(s) atualizado(s)", 
                bg=self.bg_principal, fg=self.cor_atualizado, font=("Segoe UI", 10, "bold")).pack(anchor="w")
        
        for caminho, resultado in sorted(self.resultados.items(), key=lambda x: x[0].lower()):
            atualizados = resultado['atualizados']
            if not atualizados:
                continue
            
            pasta_frame = tk.Frame(self.tab_atualizados._frame_conteudo, bg=self.bg_principal)
            pasta_frame.pack(fill="x", padx=10, pady=(10, 2))
            self._criar_label_selecionavel(pasta_frame, f"📁 {caminho}", bg=self.bg_principal, 
                    fg=self.cor_acento, font_spec=("Segoe UI", 9, "bold"))
            
            config_frame = tk.Frame(self.tab_atualizados._frame_conteudo, bg=self.bg_principal)
            config_frame.pack(fill="x", padx=20, pady=(0, 5))
            tk.Label(config_frame, text=f"Filtro: {resultado['config']['entrada'].upper()} → {resultado['config']['saida'].upper()}", 
                    bg=self.bg_principal, fg=self.fg_texto_secundario, font=("Segoe UI", 8)).pack(anchor="w")
            
            for item in atualizados:
                nome_arquivo = f"{item['nome_base']} ({item['entrada']['data']})"
                caminho_arquivo = item['entrada']['caminho']
                nome_base = item['nome_base']
                self._adicionar_item_arquivo(self.tab_atualizados._frame_conteudo, nome_arquivo, caminho, caminho_arquivo, nome_base)

    def _exportar_csv(self):
        """Exporta o relatório para um arquivo Excel (.xlsx) com hiperlinks"""
        from datetime import datetime
        
        # Pedir caminho para salvar o arquivo em Excel
        caminho_arquivo = filedialog.asksaveasfilename(
            title="Salvar Relatório como Excel",
            defaultextension=".xlsx",
            filetypes=[("Arquivo Excel", "*.xlsx"), ("Todos os arquivos", "*.*")],
            initialfile=f"relatorio_{datetime.now().strftime('%d_%m_%Y_%H%M%S')}.xlsx"
        )
        
        if not caminho_arquivo:
            return
        
        try:
            # Garantir que seja .xlsx
            if not caminho_arquivo.endswith('.xlsx'):
                caminho_arquivo = caminho_arquivo.replace('.csv', '.xlsx').replace('.xls', '.xlsx')
                if not caminho_arquivo.endswith('.xlsx'):
                    caminho_arquivo += '.xlsx'
            
            from openpyxl import Workbook
            from openpyxl.styles import Font, PatternFill, Alignment
            
            wb = Workbook()
            ws = wb.active
            ws.title = "Relatório"
            
            # Header com estilo
            headers = ['Modelo', 'Pasta', 'Status', 'Motivo']
            for col_num, header in enumerate(headers, 1):
                cell = ws.cell(row=1, column=col_num)
                cell.value = header
                cell.font = Font(bold=True, color="FFFFFF")
                cell.fill = PatternFill(start_color="5865F2", end_color="5865F2", fill_type="solid")
                cell.alignment = Alignment(horizontal="center", vertical="center")
            
            # Coletar dados de todos os arquivos
            row_num = 2
            
            for caminho_pasta, resultado in sorted(self.resultados.items(), key=lambda x: x[0].lower()):
                for tipo_lista, tipo_nome in [('novos', 'Novo'), ('desatualizados', 'Desatualizado'), ('atualizados', 'Atualizado')]:
                    itens = resultado[tipo_lista]
                    
                    for item in itens:
                        nome_base = item.get('nome_base', '')
                        caminho_arquivo_item = item['entrada']['caminho']
                        pasta_arquivo = os.path.dirname(caminho_arquivo_item)  # Pasta onde o arquivo está
                        status = 'Novo' if tipo_nome == 'Novo' else 'Desatualizado' if tipo_nome == 'Desatualizado' else 'Atualizado'
                        
                        # Verificar se existe status salvo
                        if 'status_arquivos' in self.config and caminho_arquivo_item in self.config['status_arquivos']:
                            status = self.config['status_arquivos'][caminho_arquivo_item]
                        
                        # Excluir do relatório arquivos que estão na aba de atualizados
                        # sem status definido manualmente pelo usuário
                        if tipo_lista == 'atualizados' and caminho_arquivo_item not in self.config.get('status_arquivos', {}):
                            continue
                        
                        # Se status for "Status" (padrão), marcar como "Inalterado"
                        if status == "Status":
                            status = "Inalterado"
                        
                        # Obter motivo (relatório) se existir
                        motivo = ''
                        if 'relatorios_inaptid' in self.config and caminho_arquivo_item in self.config['relatorios_inaptid']:
                            motivo = self.config['relatorios_inaptid'][caminho_arquivo_item]
                        
                        # Modelo (coluna A)
                        cell_modelo = ws.cell(row=row_num, column=1)
                        cell_modelo.value = nome_base
                        cell_modelo.alignment = Alignment(horizontal="left", vertical="center")
                        
                        # Pasta como hiperlink (coluna B)
                        cell_pasta = ws.cell(row=row_num, column=2)
                        cell_pasta.value = os.path.basename(pasta_arquivo)  # Mostrar apenas o nome da pasta
                        
                        # Criar hiperlink para abrir a pasta
                        if os.path.exists(pasta_arquivo):
                            # Converter caminho para file:/// URI
                            file_uri = 'file:///' + pasta_arquivo.replace('\\', '/').replace(' ', '%20')
                            cell_pasta.hyperlink = file_uri
                            cell_pasta.font = Font(underline="single", color="0563C1")
                        else:
                            cell_pasta.font = Font(color="808080")
                        
                        cell_pasta.alignment = Alignment(horizontal="left", vertical="center")
                        
                        # Status (coluna C)
                        cell_status = ws.cell(row=row_num, column=3)
                        cell_status.value = status
                        cell_status.alignment = Alignment(horizontal="center", vertical="center")
                        
                        # Motivo (coluna D, com wrap de texto)
                        cell_motivo = ws.cell(row=row_num, column=4)
                        cell_motivo.value = motivo
                        cell_motivo.alignment = Alignment(horizontal="left", vertical="top", wrap_text=True)
                        
                        row_num += 1
            
            # Ajustar largura das colunas
            ws.column_dimensions['A'].width = 35
            ws.column_dimensions['B'].width = 40
            ws.column_dimensions['C'].width = 15
            ws.column_dimensions['D'].width = 60
            
            # Altura adequada para header
            ws.row_dimensions[1].height = 25
            
            # Auto-ajustar altura das linhas com conteúdo
            for row in range(2, row_num):
                ws.row_dimensions[row].height = None
            
            # Salvar arquivo
            wb.save(caminho_arquivo)
            
            messagebox.showinfo("Sucesso", f"✓ Relatório exportado com sucesso!\n\n{caminho_arquivo}")
            
        except ImportError:
            messagebox.showerror("Erro", "Para exportar em Excel, instale o pacote openpyxl:\n\npip install openpyxl")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao exportar relatório:\n{str(e)}")
    
    def _ao_fechar(self):
        """Recarrega config da aplicação pai ao fechar a janela"""
        self.parent.config = carregar_config()
        self.destroy()


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
        
        # Configurar handler para fechar a janela
        self.protocol("WM_DELETE_WINDOW", self._ao_fechar_aplicacao)
        
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
        # Recarregar config do disco para garantir dados atualizados
        self.config = carregar_config()
        JanelaRelatorio(self, self.config, self.resultados, self.bg_principal, self.bg_secundario, self.fg_texto, self.fg_texto_secundario, 
                       self.filter_novos, self.filter_desatualizados, self.filter_atualizados)

    def log_console(self, msg: str):
        """Log de mensagens no console"""
        print(msg)

    def _ao_fechar_aplicacao(self):
        """Handler para quando a janela principal é fechada"""
        if messagebox.askyesno("Confirmar Saída", "Tem certeza que deseja fechar o ATLAS?"):
            self.destroy()

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
            # Resetar TODOS os status e relatórios para nova verificação limpa
            self.config['status_arquivos'] = {}
            self.config['relatorios_inaptid'] = {}
            salvar_config(self.config)
            
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
