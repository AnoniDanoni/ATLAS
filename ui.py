# -*- coding: utf-8 -*-
# ui.py - Interfaces e janelas do ATLAS

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
import os
import copy
from datetime import datetime

from core import (
    salvar_config, obter_pastas_sessao, atualizar_pastas_sessao,
    detectar_versoes_revit, abrir_revit
)


# ==================== JANELA DE SELEÇÃO DE REVIT ====================

class JanelaSelecaoRevit(tk.Toplevel):
    """Janela para seleção de versão Revit"""
    
    def __init__(self, parent, versoes):
        super().__init__(parent)
        self.title("Selecionar Revit")
        self.geometry("360x200")
        self.resizable(False, False)
        self.grab_set()
        self.transient(parent)
        self.configure(bg="#5865F2")
        
        self.versoes = versoes
        self.revit_selecionado = None
        
        self._criar_interface()

    def _criar_interface(self):
        ttk.Label(
            self,
            text="🔧 Selecionar Revit",
            font=("Segoe UI", 10, "bold"),
            background="#5865F2"
        ).pack(pady=8, padx=10)
        
        ttk.Label(
            self,
            text="Qual versão deseja usar?",
            font=("Segoe UI", 9),
            background="#5865F2"
        ).pack(pady=(0, 5))
        
        frame_lista = ttk.Frame(self)
        frame_lista.pack(fill="both", expand=True, padx=15, pady=5)
        
        scrollbar = ttk.Scrollbar(frame_lista)
        scrollbar.pack(side="right", fill="y")
        
        self.listbox = tk.Listbox(
            frame_lista,
            height=4,
            yscrollcommand=scrollbar.set,
            relief="groove",
            borderwidth=1,
            font=("Segoe UI", 9)
        )
        self.listbox.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=self.listbox.yview)
        
        for nome_versao, _ in self.versoes:
            self.listbox.insert("end", nome_versao)
        
        if self.versoes:
            self.listbox.selection_set(0)
        
        frame_botoes = ttk.Frame(self, padding="5")
        frame_botoes.pack(pady=8, fill="x", padx=15)
        
        buttons_inner = ttk.Frame(frame_botoes)
        buttons_inner.pack(anchor="center")
        
        ttk.Button(
            buttons_inner,
            text="✓ Selecionar",
            command=self._confirmar,
            width=13
        ).pack(side="left", padx=3)
        
        ttk.Button(
            buttons_inner,
            text="🗺 Mapeamento",
            command=self._fechar,
            width=13
        ).pack(side="left", padx=3)
        
        buttons_inner_2 = ttk.Frame(frame_botoes)
        buttons_inner_2.pack(anchor="center", pady=5)
        
        ttk.Button(
            buttons_inner_2,
            text="🔍 Procurar",
            command=self._fechar,
            width=13
        ).pack(side="left", padx=3)
        
        ttk.Button(
            buttons_inner_2,
            text="ℹ️ Informações",
            command=self._fechar,
            width=13
        ).pack(side="left", padx=3)
        
        buttons_inner_3 = ttk.Frame(frame_botoes)
        buttons_inner_3.pack(anchor="center", pady=5)
        
        ttk.Button(
            buttons_inner_3,
            text="✗ Fechar",
            command=self._fechar,
            width=13
        ).pack(side="left", padx=3)

    def _confirmar(self):
        sel = self.listbox.curselection()
        if not sel:
            messagebox.showinfo("Aviso", "Selecione uma versão de Revit")
            return
        
        idx = sel[0]
        self.revit_selecionado = self.versoes[idx]
        self.destroy()

    def _fechar(self):
        self.revit_selecionado = None
        self.destroy()


# ==================== JANELA DE SELEÇÃO MÚLTIPLA ====================

class JanelaSelecaoPastas(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Selecionar Pastas")
        self.geometry("600x450")
        self.resizable(False, False)
        self.grab_set()
        self.transient(parent)

        self.bg_principal = "#36393F"
        self.bg_secundario = "#2F3136"
        self.bg_terciario = "#282B30"
        self.fg_texto = "#FFFFFF"
        self.fg_texto_secundario = "#B9BBBE"
        self.cor_acento = "#5865F2"
        
        self.configure(bg=self.bg_principal)
        self.pastas_selecionadas = []
        self._criar_interface()

    def _criar_interface(self):
        # Header com instruções
        header_frame = tk.Frame(self, bg=self.bg_secundario)
        header_frame.pack(fill="x", pady=(0, 10))
        
        ttk.Label(header_frame, text="📁 Selecionar Pastas para Monitorar", font=("Segoe UI", 11, "bold"), 
                 background=self.bg_secundario, foreground=self.cor_acento).pack(pady=8, padx=10, anchor="w")
        
        ttk.Label(header_frame, text="Use Ctrl+Click para multiselect e Shift+Click para selecionar um intervalo", 
                 font=("Segoe UI", 8), background=self.bg_secundario, foreground=self.fg_texto_secundario).pack(pady=(0, 8), padx=10, anchor="w")
        
        # Lista de pastas com suporte a multiselect
        frame_lista_border = tk.Frame(self, bg=self.cor_acento)
        frame_lista_border.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        frame_lista = tk.Frame(frame_lista_border, bg=self.bg_principal)
        frame_lista.pack(fill="both", expand=True, padx=2, pady=2)

        scrollbar = ttk.Scrollbar(frame_lista)
        scrollbar.pack(side="right", fill="y")

        # selectmode=tk.EXTENDED permite Ctrl+Click e Shift+Click para multiselect
        self.listbox = tk.Listbox(frame_lista, height=15, yscrollcommand=scrollbar.set, relief="flat", borderwidth=0, 
                                   bg=self.bg_terciario, fg=self.fg_texto, selectbackground=self.cor_acento, 
                                   selectforeground="#ffffff", font=("Segoe UI", 9), selectmode=tk.EXTENDED)
        self.listbox.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=self.listbox.yview)

        frame_botoes = tk.Frame(self, bg=self.bg_principal)
        frame_botoes.pack(pady=10)

        ttk.Button(frame_botoes, text="➕ Adicionar Pasta", command=self._adicionar_pasta, width=20).grid(row=0, column=0, padx=5)
        ttk.Button(frame_botoes, text="➖ Remover Selecionada(s)", command=self._remover_pasta, width=20).grid(row=0, column=1, padx=5)
        ttk.Button(frame_botoes, text="✓ Confirmar", command=self._confirmar, width=20).grid(row=1, column=0, padx=5, pady=5)
        ttk.Button(frame_botoes, text="✗ Cancelar", command=self.destroy, width=20).grid(row=1, column=1, padx=5, pady=5)

    def _adicionar_pasta(self):
        caminho = filedialog.askdirectory(title="Selecione uma pasta")
        if caminho and caminho not in self.pastas_selecionadas:
            self.pastas_selecionadas.append(caminho)
            self.listbox.insert("end", caminho)

    def _remover_pasta(self):
        # Remover todas as pastas selecionadas (suporta multiselect)
        selecionadas = self.listbox.curselection()
        if selecionadas:
            # Remover em ordem reversa para não afetar os índices
            for idx in reversed(selecionadas):
                self.listbox.delete(idx)
                self.pastas_selecionadas.pop(idx)

    def _confirmar(self):
        # Atualizar pastas_selecionadas com base no que está na listbox
        self.pastas_selecionadas = list(self.listbox.get(0, "end"))
        self.destroy()


# ==================== JANELA DE GERENCIAMENTO DE SESSÕES ====================

class JanelaGerenciarSessoes(tk.Toplevel):
    def __init__(self, parent, config, bg_principal="#36393F", bg_secundario="#2F3136", fg_texto="#FFFFFF", fg_texto_secundario="#B9BBBE"):
        super().__init__(parent)
        self.title("Gerenciar Sessões")
        self.geometry("500x450")
        self.resizable(False, False)
        self.grab_set()
        self.transient(parent)
        
        self.parent_app = parent
        self.config = config
        self.sessao_modificada = False
        
        self.bg_principal = bg_principal
        self.bg_secundario = bg_secundario
        self.bg_terciario = "#282B30"
        self.fg_texto = fg_texto
        self.fg_texto_secundario = fg_texto_secundario
        self.cor_acento = "#5865F2"
        
        self.configure(bg=self.bg_principal)
        
        self._criar_interface()
        self._atualizar_lista()

    def _criar_interface(self):
        header_frame = tk.Frame(self, bg=self.bg_secundario)
        header_frame.pack(fill="x", pady=(0, 10))
        
        ttk.Label(header_frame, text="📋 Sessões Configuradas", font=("Segoe UI", 12, "bold"), background=self.bg_secundario, foreground=self.cor_acento).pack(pady=10)
        
        frame_lista_border = tk.Frame(self, bg=self.cor_acento)
        frame_lista_border.pack(fill="both", expand=True, padx=10, pady=10)
        
        frame_lista = tk.Frame(frame_lista_border, bg=self.bg_principal)
        frame_lista.pack(fill="both", expand=True, padx=2, pady=2)
        
        scrollbar = ttk.Scrollbar(frame_lista)
        scrollbar.pack(side="right", fill="y")
        
        self.listbox = tk.Listbox(frame_lista, height=12, yscrollcommand=scrollbar.set, 
                                   relief="flat", borderwidth=0, bg=self.bg_terciario, fg=self.fg_texto,
                                   selectbackground=self.cor_acento, selectforeground="#ffffff", font=("Segoe UI", 9))
        self.listbox.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=self.listbox.yview)
        
        frame_botoes = tk.Frame(self, bg=self.bg_principal)
        frame_botoes.pack(pady=10)
        
        ttk.Button(frame_botoes, text="➕ Nova Sessão", command=self._nova_sessao, width=18).grid(row=0, column=0, padx=4, pady=3)
        ttk.Button(frame_botoes, text="✏️ Renomear", command=self._renomear_sessao, width=18).grid(row=0, column=1, padx=4, pady=3)
        ttk.Button(frame_botoes, text="📋 Duplicar", command=self._duplicar_sessao, width=18).grid(row=1, column=0, padx=4, pady=3)
        ttk.Button(frame_botoes, text="🗑 Excluir", command=self._excluir_sessao, width=18).grid(row=1, column=1, padx=4, pady=3)
        ttk.Button(frame_botoes, text="✓ Fechar", command=self._fechar, width=37).grid(row=2, column=0, columnspan=2, padx=4, pady=10)

    def _atualizar_lista(self):
        self.listbox.delete(0, "end")
        sessao_ativa = self.config['sessao_ativa']
        for nome_sessao in sorted(self.config['sessoes'].keys()):
            qtd_pastas = len(self.config['sessoes'][nome_sessao]['pastas'])
            marcador = "★" if nome_sessao == sessao_ativa else "  "
            self.listbox.insert("end", f"{marcador} {nome_sessao} ({qtd_pastas} pasta(s))")

    def _nova_sessao(self):
        nome = simpledialog.askstring("Nova Sessão", "Nome da nova sessão:", parent=self)
        if not nome:
            return
        
        nome = nome.strip()
        if nome in self.config['sessoes']:
            messagebox.showerror("Erro", "Já existe uma sessão com este nome!")
            return
        
        self.config['sessoes'][nome] = {
            'data_criacao': datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
            'pastas': []
        }
        self.sessao_modificada = True
        self._atualizar_lista()
        messagebox.showinfo("Sucesso", f"Sessão '{nome}' criada com sucesso!")

    def _renomear_sessao(self):
        sel = self.listbox.curselection()
        if not sel:
            messagebox.showinfo("Aviso", "Selecione uma sessão para renomear")
            return
        
        idx = sel[0]
        nome_antigo = list(self.config['sessoes'].keys())[idx]
        
        novo_nome = simpledialog.askstring("Renomear Sessão", 
                                            f"Novo nome para '{nome_antigo}':", 
                                            initialvalue=nome_antigo,
                                            parent=self)
        if not novo_nome or novo_nome == nome_antigo:
            return
        
        novo_nome = novo_nome.strip()
        if novo_nome in self.config['sessoes']:
            messagebox.showerror("Erro", "Já existe uma sessão com este nome!")
            return
        
        self.config['sessoes'][novo_nome] = self.config['sessoes'].pop(nome_antigo)
        
        if self.config['sessao_ativa'] == nome_antigo:
            self.config['sessao_ativa'] = novo_nome
        
        self.sessao_modificada = True
        self._atualizar_lista()
        messagebox.showinfo("Sucesso", f"Sessão renomeada para '{novo_nome}'")

    def _duplicar_sessao(self):
        sel = self.listbox.curselection()
        if not sel:
            messagebox.showinfo("Aviso", "Selecione uma sessão para duplicar")
            return
        
        idx = sel[0]
        nome_original = list(self.config['sessoes'].keys())[idx]
        
        novo_nome = simpledialog.askstring("Duplicar Sessão", 
                                            f"Nome para a cópia de '{nome_original}':",
                                            initialvalue=f"{nome_original} (cópia)",
                                            parent=self)
        if not novo_nome:
            return
        
        novo_nome = novo_nome.strip()
        if novo_nome in self.config['sessoes']:
            messagebox.showerror("Erro", "Já existe uma sessão com este nome!")
            return
        
        self.config['sessoes'][novo_nome] = copy.deepcopy(self.config['sessoes'][nome_original])
        self.config['sessoes'][novo_nome]['data_criacao'] = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        
        self.sessao_modificada = True
        self._atualizar_lista()
        messagebox.showinfo("Sucesso", f"Sessão duplicada como '{novo_nome}'")

    def _excluir_sessao(self):
        sel = self.listbox.curselection()
        if not sel:
            messagebox.showinfo("Aviso", "Selecione uma sessão para excluir")
            return
        
        idx = sel[0]
        nome = list(self.config['sessoes'].keys())[idx]
        
        if len(self.config['sessoes']) == 1:
            messagebox.showerror("Erro", "Não é possível excluir a última sessão!")
            return
        
        if not messagebox.askyesno("Confirmar", f"Excluir sessão '{nome}'?"):
            return
        
        if self.config['sessao_ativa'] == nome:
            outras = [s for s in self.config['sessoes'].keys() if s != nome]
            self.config['sessao_ativa'] = outras[0]
        
        del self.config['sessoes'][nome]
        self.sessao_modificada = True
        self._atualizar_lista()
        messagebox.showinfo("Sucesso", f"Sessão '{nome}' excluída")

    def _fechar(self):
        if self.sessao_modificada:
            salvar_config(self.config)
            self.parent_app.carregar_sessao_ativa()
        self.destroy()


# ==================== JANELA DE GERENCIAMENTO DE PASTAS ====================

class JanelaGerenciarPastas(tk.Toplevel):
    def __init__(self, parent, config, bg_principal="#36393F", bg_secundario="#2F3136", fg_texto="#FFFFFF", fg_texto_secundario="#B9BBBE"):
        super().__init__(parent)
        self.title("Gerenciar Pastas")
        self.geometry("650x630")
        self.resizable(False, False)
        self.grab_set()
        self.transient(parent)
        
        self.parent_app = parent
        self.config = config
        self.pastas_modificadas = False
        self.pasta_selecionada_ignorados = None
        self.ignorados_selecionados = set()
        self.botoes_ignorados = {}
        
        self.bg_principal = bg_principal
        self.bg_secundario = bg_secundario
        self.bg_terciario = "#282B30"
        self.fg_texto = fg_texto
        self.fg_texto_secundario = fg_texto_secundario
        self.cor_acento = "#5865F2"
        
        self.configure(bg=self.bg_principal)
        
        self._criar_interface()
        self._atualizar_lista()
        
        self.bind("<Delete>", self._ao_pressionar_del_global)

    def _ao_pressionar_delete_lista(self, event):
        """Remove pasta(s) selecionada(s) quando DEL é pressionado na listbox"""
        selecionadas = self.listbox.curselection()
        if not selecionadas:
            return
        
        sessao_ativa = self.parent_app.sessao_atual
        pastas = obter_pastas_sessao(self.config, sessao_ativa)
        
        # Criar mensagem de confirmação
        qtd_pastas = len(selecionadas)
        if qtd_pastas == 1:
            pasta = pastas[selecionadas[0]]
            msg = f"Remover pasta?\n{pasta['caminho']}"
        else:
            msg = f"Remover {qtd_pastas} pastas selecionadas?"
        
        if not messagebox.askyesno("Confirmar", msg):
            return
        
        # Remover em ordem reversa para não afetar os índices
        for idx in reversed(selecionadas):
            if idx < len(pastas):
                pastas.pop(idx)
        
        atualizar_pastas_sessao(self.config, sessao_ativa, pastas)
        salvar_config(self.config)
        self._atualizar_lista()

    def _ao_pressionar_del_global(self, event):
        """Remove todos os ignorados selecionados quando DEL é pressionado"""
        if not self.ignorados_selecionados:
            return
        
        sel = self.listbox.curselection()
        if not sel:
            return
        
        idx = sel[0]
        sessao_ativa = self.parent_app.sessao_atual
        pastas = obter_pastas_sessao(self.config, sessao_ativa)
        pasta = pastas[idx]
        caminho_pasta = pasta['caminho']
        
        if 'arquivos_ignorados' not in self.config or caminho_pasta not in self.config['arquivos_ignorados']:
            return
        
        for arquivo in self.ignorados_selecionados:
            if arquivo in self.config['arquivos_ignorados'][caminho_pasta]:
                self.config['arquivos_ignorados'][caminho_pasta].remove(arquivo)
        
        salvar_config(self.config)
        self._ao_selecionar_pasta()

    def _criar_interface(self):
        header_frame = tk.Frame(self, bg=self.bg_secundario)
        header_frame.pack(fill="x", pady=(0, 10))
        
        ttk.Label(header_frame, text="📁 Pastas Monitoradas", font=("Segoe UI", 12, "bold"), background=self.bg_secundario, foreground=self.cor_acento).pack(pady=10)
        
        frame_lista_border = tk.Frame(self, bg=self.cor_acento)
        frame_lista_border.pack(fill="both", expand=True, padx=10, pady=(10, 5))
        
        frame_lista = tk.Frame(frame_lista_border, bg=self.bg_principal)
        frame_lista.pack(fill="both", expand=True, padx=2, pady=2)
        
        scrollbar = ttk.Scrollbar(frame_lista)
        scrollbar.pack(side="right", fill="y")
        
        self.listbox = tk.Listbox(frame_lista, height=8, yscrollcommand=scrollbar.set, 
                                   relief="flat", borderwidth=0, bg=self.bg_terciario, fg=self.fg_texto,
                                   selectbackground=self.cor_acento, selectforeground="#ffffff", font=("Segoe UI", 9),
                                   selectmode=tk.EXTENDED)
        self.listbox.pack(side="left", fill="both", expand=True)
        self.listbox.bind("<<ListboxSelect>>", self._ao_selecionar_pasta)
        self.listbox.bind("<Delete>", self._ao_pressionar_delete_lista)
        scrollbar.config(command=self.listbox.yview)
        
        frame_ignorados_label = tk.Frame(self, bg=self.bg_principal)
        frame_ignorados_label.pack(anchor="w", padx=10, pady=(5, 2))
        ttk.Label(frame_ignorados_label, text="📋 Arquivos Ignorados:", font=("Segoe UI", 10, "bold"), background=self.bg_principal, foreground=self.fg_texto).pack(anchor="w")
        
        frame_ignorados_border = tk.Frame(self, bg=self.cor_acento)
        frame_ignorados_border.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        frame_ignorados_scroll = tk.Frame(frame_ignorados_border, bg=self.bg_principal)
        frame_ignorados_scroll.pack(fill="both", expand=True, padx=2, pady=2)
        
        scrollbar_ignorados = ttk.Scrollbar(frame_ignorados_scroll)
        scrollbar_ignorados.pack(side="right", fill="y")
        
        self.canvas_ignorados = tk.Canvas(frame_ignorados_scroll, bg=self.bg_principal, highlightthickness=0, yscrollcommand=scrollbar_ignorados.set)
        self.canvas_ignorados.pack(side="left", fill="both", expand=True)
        scrollbar_ignorados.config(command=self.canvas_ignorados.yview)
        
        self.frame_botoes_ignorados = tk.Frame(self.canvas_ignorados, bg=self.bg_principal)
        self.canvas_window = self.canvas_ignorados.create_window((0, 0), window=self.frame_botoes_ignorados, anchor="nw")
        
        def _ao_mudar_frame_ignorados(event):
            self.canvas_ignorados.configure(scrollregion=self.canvas_ignorados.bbox("all"))
        
        self.frame_botoes_ignorados.bind("<Configure>", _ao_mudar_frame_ignorados)
        
        self.botoes_ignorados = {}
        self.ignorados_selecionados = set()
        
        frame_botoes = tk.Frame(self, bg=self.bg_principal)
        frame_botoes.pack(pady=10)
        
        ttk.Button(frame_botoes, text="➕ Adicionar", command=self._adicionar_pasta, width=18).grid(row=0, column=0, padx=4, pady=3)
        ttk.Button(frame_botoes, text="✏️ Editar", command=self._editar_pasta, width=18).grid(row=0, column=1, padx=4, pady=3)
        ttk.Button(frame_botoes, text="✓ Fechar", command=self._fechar, width=37).grid(row=1, column=0, columnspan=2, padx=4, pady=10)

    def _atualizar_lista(self):
        self.listbox.delete(0, "end")
        sessao_ativa = self.parent_app.sessao_atual
        pastas = obter_pastas_sessao(self.config, sessao_ativa)
        for pasta in pastas:
            self.listbox.insert("end", f"{pasta['caminho']} ({pasta['entrada']} → {pasta['saida']})")
        
        if not pastas:
            self._limpar_botoes_ignorados()
    
    def _limpar_botoes_ignorados(self):
        """Remove todos os botões e labels de arquivos ignorados"""
        for widget in self.frame_botoes_ignorados.winfo_children():
            widget.destroy()
        self.botoes_ignorados.clear()
        self.ignorados_selecionados.clear()
    
    def _ao_selecionar_pasta(self, event=None):
        """Mostra os arquivos ignorados da pasta selecionada como botões"""
        self._limpar_botoes_ignorados()
        
        sel = self.listbox.curselection()
        if not sel:
            return
        
        idx = sel[0]
        sessao_ativa = self.parent_app.sessao_atual
        pastas = obter_pastas_sessao(self.config, sessao_ativa)
        pasta = pastas[idx]
        caminho_pasta = pasta['caminho']
        
        if 'arquivos_ignorados' not in self.config or caminho_pasta not in self.config['arquivos_ignorados']:
            lbl = tk.Label(self.frame_botoes_ignorados, text="Nenhum arquivo ignorado", 
                          bg=self.bg_principal, fg=self.fg_texto, font=("Segoe UI", 8))
            lbl.pack(anchor="w", padx=5, pady=2)
            return
        
        ignorados = self.config['arquivos_ignorados'][caminho_pasta]
        self.pasta_selecionada_ignorados = caminho_pasta
        
        if not ignorados:
            lbl = tk.Label(self.frame_botoes_ignorados, text="Nenhum arquivo ignorado", 
                          bg=self.bg_principal, fg=self.fg_texto, font=("Segoe UI", 8))
            lbl.pack(anchor="w", padx=5, pady=2)
        else:
            for arquivo in ignorados:
                self._criar_botao_ignorado(arquivo, caminho_pasta)

    def _criar_botao_ignorado(self, arquivo, caminho_pasta):
        """Cria um botão para um arquivo ignorado que pode ser clicado para remover"""
        def ao_clicar_botao_com_modificadores(event):
            ctrl_pressionado = event.state & 0x0004
            shift_pressionado = event.state & 0x0001
            
            if not ctrl_pressionado and not shift_pressionado:
                self.ignorados_selecionados.clear()
                for nome, b in self.botoes_ignorados.items():
                    b.config(bg=self.bg_terciario, fg=self.fg_texto_secundario, relief="flat")
                self.ignorados_selecionados.add(arquivo)
                btn.config(bg=self.cor_acento, fg=self.fg_texto, relief="sunken")
            elif ctrl_pressionado:
                if arquivo in self.ignorados_selecionados:
                    self.ignorados_selecionados.remove(arquivo)
                    btn.config(bg=self.bg_terciario, fg=self.fg_texto_secundario, relief="flat")
                else:
                    self.ignorados_selecionados.add(arquivo)
                    btn.config(bg=self.cor_acento, fg=self.fg_texto, relief="sunken")
            elif shift_pressionado:
                if self.ignorados_selecionados:
                    ultimo = list(self.ignorados_selecionados)[-1]
                    sel = self.listbox.curselection()
                    if sel:
                        idx = sel[0]
                        sessao_ativa = self.parent_app.sessao_atual
                        pastas = obter_pastas_sessao(self.config, sessao_ativa)
                        pasta = pastas[idx]
                        caminho_pasta_selecionada = pasta['caminho']
                        
                        if 'arquivos_ignorados' in self.config and caminho_pasta_selecionada in self.config['arquivos_ignorados']:
                            arquivos = self.config['arquivos_ignorados'][caminho_pasta_selecionada]
                            inicio = arquivos.index(ultimo) if ultimo in arquivos else 0
                            fim = arquivos.index(arquivo) if arquivo in arquivos else 0
                            
                            if inicio > fim:
                                inicio, fim = fim, inicio
                            
                            for nome, b in self.botoes_ignorados.items():
                                b.config(bg=self.bg_terciario, fg=self.fg_texto_secundario, relief="flat")
                            
                            self.ignorados_selecionados.clear()
                            for i in range(inicio, fim + 1):
                                if i < len(arquivos):
                                    self.ignorados_selecionados.add(arquivos[i])
                                    if arquivos[i] in self.botoes_ignorados:
                                        self.botoes_ignorados[arquivos[i]].config(bg=self.cor_acento, fg=self.fg_texto, relief="sunken")
                else:
                    self.ignorados_selecionados.add(arquivo)
                    btn.config(bg=self.cor_acento, fg=self.fg_texto, relief="sunken")
        
        def ao_clicar_direito(event):
            if 'arquivos_ignorados' in self.config and caminho_pasta in self.config['arquivos_ignorados']:
                if arquivo in self.config['arquivos_ignorados'][caminho_pasta]:
                    self.config['arquivos_ignorados'][caminho_pasta].remove(arquivo)
                    salvar_config(self.config)
                    self._ao_selecionar_pasta()
        
        btn = tk.Button(self.frame_botoes_ignorados, text=f"  • {arquivo}  ", 
                       bg=self.bg_terciario, fg=self.fg_texto_secundario, 
                       relief="flat", font=("Segoe UI", 8), 
                       padx=5, pady=3, anchor="w", justify="left")
        btn.pack(anchor="w", padx=5, pady=2, fill="x")
        btn.bind("<Button-1>", ao_clicar_botao_com_modificadores)
        btn.bind("<Button-3>", ao_clicar_direito)
        self.botoes_ignorados[arquivo] = btn

    def _adicionar_pasta(self):
        caminho = filedialog.askdirectory(title="Selecione uma pasta para monitorar")
        if not caminho:
            return
        
        sessao_ativa = self.parent_app.sessao_atual
        pastas = obter_pastas_sessao(self.config, sessao_ativa)
        
        if any(p['caminho'] == caminho for p in pastas):
            messagebox.showwarning("Aviso", "Esta pasta já está sendo monitorada!")
            return
        
        extensoes = self._pedir_extensoes()
        if not extensoes:
            return
        
        pastas.append({
            "caminho": caminho,
            "entrada": extensoes['entrada'],
            "saida": extensoes['saida']
        })
        
        atualizar_pastas_sessao(self.config, sessao_ativa, pastas)
        salvar_config(self.config)
        self.pastas_modificadas = True
        self._atualizar_lista()
        self._ao_selecionar_pasta()
        messagebox.showinfo("Sucesso", "Pasta adicionada com sucesso!")

    def _editar_pasta(self):
        selecionadas = self.listbox.curselection()
        if not selecionadas:
            messagebox.showinfo("Aviso", "Selecione uma ou mais pastas para editar")
            return
        
        # Se apenas uma pasta selecionada, editar individual
        if len(selecionadas) == 1:
            idx = selecionadas[0]
            sessao_ativa = self.parent_app.sessao_atual
            pastas = obter_pastas_sessao(self.config, sessao_ativa)
            pasta = pastas[idx]
            
            extensoes = self._pedir_extensoes(pasta['entrada'], pasta['saida'])
            if not extensoes:
                return
            
            pasta['entrada'] = extensoes['entrada']
            pasta['saida'] = extensoes['saida']
            
            atualizar_pastas_sessao(self.config, sessao_ativa, pastas)
            salvar_config(self.config)
            self.pastas_modificadas = True
            self._atualizar_lista()
            self._ao_selecionar_pasta()
            messagebox.showinfo("Sucesso", "Pasta atualizada com sucesso!")
        else:
            # Se múltiplas pastas, pedir extensões e aplicar a todas
            sessao_ativa = self.parent_app.sessao_atual
            pastas = obter_pastas_sessao(self.config, sessao_ativa)
            
            if not messagebox.askyesno("Editar Múltiplas", f"Aplicar as mesmas extensões para {len(selecionadas)} pastas?"):
                return
            
            # Usar extensões da primeira pasta selecionada como padrão
            primeira_pasta = pastas[selecionadas[0]]
            extensoes = self._pedir_extensoes(primeira_pasta['entrada'], primeira_pasta['saida'])
            if not extensoes:
                return
            
            # Aplicar a todas as pastas selecionadas
            for idx in selecionadas:
                if idx < len(pastas):
                    pastas[idx]['entrada'] = extensoes['entrada']
                    pastas[idx]['saida'] = extensoes['saida']
            
            atualizar_pastas_sessao(self.config, sessao_ativa, pastas)
            salvar_config(self.config)
            self.pastas_modificadas = True
            self._atualizar_lista()
            self._ao_selecionar_pasta()
            messagebox.showinfo("Sucesso", f"✓ {len(selecionadas)} pastas atualizadas com sucesso!")

    def _pedir_extensoes(self, entrada_padrao="rvt", saida_padrao="ifc"):
        """Abre diálogo para escolher extensões e salva as preferências"""
        dialog = tk.Toplevel(self)
        dialog.title("Escolher Extensões")
        dialog.geometry("350x280")
        dialog.resizable(False, False)
        dialog.grab_set()
        dialog.transient(self)
        dialog.configure(bg=self.bg_principal)
        
        # Usar últimas extensões salvas se disponíveis
        if 'ultimas_extensoes' in self.config:
            entrada_padrao = self.config['ultimas_extensoes'].get('entrada', entrada_padrao)
            saida_padrao = self.config['ultimas_extensoes'].get('saida', saida_padrao)
        
        ttk.Label(dialog, text="Extensões", font=("Segoe UI", 11, "bold"), background=self.bg_principal, foreground=self.cor_acento).pack(pady=10)
        
        frame = tk.Frame(dialog, bg=self.bg_principal)
        frame.pack(padx=20, pady=10, fill="both", expand=True)
        
        ttk.Label(frame, text="Extensão de Entrada:", font=("Segoe UI", 10), background=self.bg_principal, foreground=self.fg_texto).pack(anchor="w", pady=(0, 5))
        entrada_var = tk.StringVar(value=entrada_padrao)
        entrada_combo = ttk.Combobox(frame, textvariable=entrada_var, values=["dwg", "rvt", "rfa"], state="readonly", width=30)
        entrada_combo.pack(anchor="w", pady=(0, 15))
        
        ttk.Label(frame, text="Extensão de Saída:", font=("Segoe UI", 10), background=self.bg_principal, foreground=self.fg_texto).pack(anchor="w", pady=(0, 5))
        saida_var = tk.StringVar(value=saida_padrao)
        saida_combo = ttk.Combobox(frame, textvariable=saida_var, values=["ifc", "nwc"], state="readonly", width=30)
        saida_combo.pack(anchor="w")
        
        resultado = [None]
        
        def confirmar():
            resultado[0] = {'entrada': entrada_var.get(), 'saida': saida_var.get()}
            
            # Salvar as últimas extensões escolhidas
            if 'ultimas_extensoes' not in self.config:
                self.config['ultimas_extensoes'] = {}
            
            self.config['ultimas_extensoes']['entrada'] = entrada_var.get()
            self.config['ultimas_extensoes']['saida'] = saida_var.get()
            salvar_config(self.config)
            
            dialog.destroy()
        
        btn_frame = tk.Frame(dialog, bg=self.bg_principal)
        btn_frame.pack(pady=10, fill="x", padx=20)
        
        ttk.Button(btn_frame, text="Cancelar", command=dialog.destroy, width=15).pack(side="right", padx=(5, 0))
        ttk.Button(btn_frame, text="✓ OK", command=confirmar, width=15).pack(side="right")
        
        self.wait_window(dialog)
        return resultado[0]

    def _fechar(self):
        if self.pastas_modificadas:
            self.parent_app.carregar_sessao_ativa()
        self.destroy()
