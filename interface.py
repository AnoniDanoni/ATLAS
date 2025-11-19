# -*- coding: utf-8 -*-
# monitor.py
# Versão atualizada: lembra a última extensão escolhida (entrada/saída) e persiste no arquivo de configuração.

import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext, messagebox, simpledialog
import threading
import subprocess
import os
import json
from datetime import datetime
from pathlib import Path
import set  # seu módulo set.py

# ==================== CONFIGURAÇÃO DE DIRETÓRIO ====================

def obter_diretorio_atlas():
    """
    Retorna o caminho do diretório Atlas em AppData/Local.
    Cria o diretório se não existir.
    """
    # Usa AppData/Local para dados de aplicação no Windows
    appdata_local = os.getenv('LOCALAPPDATA')
    
    if appdata_local:
        # Caminho: C:\Users\[Usuario]\AppData\Local\Atlas
        diretorio_atlas = os.path.join(appdata_local, 'Atlas')
    else:
        # Fallback para C:\Atlas se LOCALAPPDATA não estiver disponível
        diretorio_atlas = r'C:\Atlas'
    
    # Cria o diretório se não existir
    try:
        os.makedirs(diretorio_atlas, exist_ok=True)
        print(f"[INFO] Diretório Atlas: {diretorio_atlas}")
    except Exception as e:
        print(f"[ERRO] Não foi possível criar diretório Atlas: {e}")
        # Usa diretório atual como último recurso
        diretorio_atlas = os.getcwd()
    
    return diretorio_atlas


# Define o caminho completo do arquivo de configuração
DIRETORIO_ATLAS = obter_diretorio_atlas()
CONFIG_FILE = os.path.join(DIRETORIO_ATLAS, "config_pastas.json")


# ==================== FUNÇÕES DE CONFIGURAÇÃO COM SESSÕES ====================

def carregar_config():
    """Carrega todas as sessões do arquivo de config"""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
                print(f"[INFO] Configuração carregada de: {CONFIG_FILE}")
                return config
        except Exception as e:
            print(f"[ERRO] Erro ao carregar config: {e}")
    
    # Estrutura padrão com uma sessão inicial
    print(f"[INFO] Criando nova configuração padrão")
    return {
        'sessao_ativa': 'Padrão',
        'sessoes': {
            'Padrão': {
                'data_criacao': datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                'pastas': []
            }
        },
        # Adiciona here a persistência das últimas extensões usadas.
        'ultimas_extensoes': {
            'entrada': 'rvt',
            'saida': 'ifc'
        }
    }


def salvar_config(config_completo):
    """Salva toda a configuração incluindo todas as sessões"""
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config_completo, f, indent=2, ensure_ascii=False)
        print(f"[INFO] Configuração salva em: {CONFIG_FILE}")
    except Exception as e:
        print(f"[ERRO] Erro ao salvar config: {e}")
        messagebox.showerror("Erro", f"Não foi possível salvar configuração:\n{e}")


def obter_pastas_sessao(config, nome_sessao):
    """Retorna a lista de pastas de uma sessão específica"""
    return config['sessoes'].get(nome_sessao, {}).get('pastas', [])


def atualizar_pastas_sessao(config, nome_sessao, pastas):
    """Atualiza as pastas de uma sessão específica"""
    if nome_sessao in config['sessoes']:
        config['sessoes'][nome_sessao]['pastas'] = pastas
        config['sessoes'][nome_sessao]['ultima_modificacao'] = datetime.now().strftime("%d/%m/%Y %H:%M:%S")


# ==================== FUNÇÕES DO MONITOR (mantidas) ====================

def extrair_nome_base(nome_arquivo, extensao_alvo):
    nome = nome_arquivo
    if nome.lower().endswith(f'.{extensao_alvo.lower()}'):
        nome = nome[:-len(extensao_alvo) - 1]
    while True:
        base, ext = os.path.splitext(nome)
        if ext:
            nome = base
        else:
            break
    return nome


def escanear_pasta(caminho, extensao):
    arquivos = {}
    try:
        # Verifica apenas os arquivos no diretório raiz, não nas subpastas
        for nome in os.listdir(caminho):
            caminho_completo = os.path.join(caminho, nome)
            if os.path.isfile(caminho_completo) and nome.lower().endswith(f'.{extensao.lower()}'):
                nome_base = extrair_nome_base(nome, extensao)
                try:
                    timestamp = os.path.getmtime(caminho_completo)
                    arquivos[nome_base] = {
                        'nome': nome,
                        'caminho': caminho_completo,
                        'data': datetime.fromtimestamp(timestamp).strftime("%d/%m/%Y %H:%M"),
                        'timestamp': timestamp
                    }
                except:
                    pass
    except PermissionError:
        # Caso não tenha permissão para acessar a pasta
        pass
    except FileNotFoundError:
        # Caso a pasta não exista mais
        pass
    
    return arquivos


def verificar_atualizacoes(pastas_config):
    resultados_por_pasta = {}
    for config in pastas_config:
        caminho = config['caminho']
        entrada_ext = config['entrada']
        saida_ext = config['saida']

        arquivos_entrada = escanear_pasta(caminho, entrada_ext)
        arquivos_saida = escanear_pasta(caminho, saida_ext)

        desatualizados = []
        novos = []
        atualizados = []

        for nome_base, info_entrada in arquivos_entrada.items():
            if nome_base in arquivos_saida:
                info_saida = arquivos_saida[nome_base]
                diff_seg = info_entrada['timestamp'] - info_saida['timestamp']
                diff_dias = diff_seg / 86400
                if diff_seg > 3600:
                    desatualizados.append({
                        'nome_base': nome_base,
                        'entrada': info_entrada,
                        'saida': info_saida,
                        'dias': round(diff_dias, 1),
                        'filtro_entrada': entrada_ext,
                        'filtro_saida': saida_ext
                    })
                else:
                    atualizados.append({
                        'nome_base': nome_base,
                        'entrada': info_entrada,
                        'saida': info_saida
                    })
            else:
                novos.append({
                    'nome_base': nome_base,
                    'entrada': info_entrada,
                    'filtro_entrada': entrada_ext,
                    'filtro_saida': saida_ext
                })

        resultados_por_pasta[caminho] = {
            'config': config,
            'novos': novos,
            'desatualizados': desatualizados,
            'atualizados': atualizados,
            'total_entrada': len(arquivos_entrada),
            'total_saida': len(arquivos_saida)
        }
    return resultados_por_pasta


# ==================== JANELA DE SELEÇÃO MÚLTIPLA ====================

class JanelaSelecaoPastas(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Selecionar Pastas")
        self.geometry("600x400")
        self.resizable(False, False)
        self.grab_set()
        self.transient(parent)

        self.pastas_selecionadas = []
        self._criar_interface()

    def _criar_interface(self):
        ttk.Label(self, text="Pastas Selecionadas:", font=("Segoe UI", 11, "bold")).pack(pady=10, padx=10, anchor="w")
        frame_lista = ttk.Frame(self)
        frame_lista.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        scrollbar = ttk.Scrollbar(frame_lista)
        scrollbar.pack(side="right", fill="y")

        self.listbox = tk.Listbox(frame_lista, height=15, yscrollcommand=scrollbar.set, relief="groove", borderwidth=2)
        self.listbox.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=self.listbox.yview)

        frame_botoes = ttk.Frame(self)
        frame_botoes.pack(pady=10)

        ttk.Button(frame_botoes, text="➕ Adicionar Pasta", command=self._adicionar_pasta, width=20).grid(row=0, column=0, padx=5)
        ttk.Button(frame_botoes, text="➖ Remover Selecionada", command=self._remover_pasta, width=20).grid(row=0, column=1, padx=5)
        ttk.Button(frame_botoes, text="✓ Confirmar", command=self._confirmar, width=20).grid(row=1, column=0, padx=5, pady=5)
        ttk.Button(frame_botoes, text="✗ Cancelar", command=self.destroy, width=20).grid(row=1, column=1, padx=5, pady=5)

    def _adicionar_pasta(self):
        caminho = filedialog.askdirectory(title="Selecione uma pasta")
        if caminho and caminho not in self.pastas_selecionadas:
            self.pastas_selecionadas.append(caminho)
            self.listbox.insert("end", caminho)

    def _remover_pasta(self):
        sel = self.listbox.curselection()
        if sel:
            idx = sel[0]
            self.listbox.delete(idx)
            self.pastas_selecionadas.pop(idx)

    def _confirmar(self):
        self.destroy()


# ==================== JANELA DE GERENCIAMENTO DE SESSÕES ====================

class JanelaGerenciarSessoes(tk.Toplevel):
    def __init__(self, parent, config):
        super().__init__(parent)
        self.title("Gerenciar Sessões")
        self.geometry("500x450")
        self.resizable(False, False)
        self.grab_set()
        self.transient(parent)
        
        self.parent_app = parent
        self.config = config
        self.sessao_modificada = False
        
        self._criar_interface()
        self._atualizar_lista()

    def _criar_interface(self):
        ttk.Label(self, text="📋 Sessões Configuradas", font=("Segoe UI", 12, "bold")).pack(pady=10)
        
        # Frame da lista
        frame_lista = ttk.Frame(self)
        frame_lista.pack(fill="both", expand=True, padx=10, pady=10)
        
        scrollbar = ttk.Scrollbar(frame_lista)
        scrollbar.pack(side="right", fill="y")
        
        self.listbox = tk.Listbox(frame_lista, height=12, yscrollcommand=scrollbar.set, 
                                   relief="groove", borderwidth=2)
        self.listbox.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=self.listbox.yview)
        
        # Frame de botões
        frame_botoes = ttk.Frame(self)
        frame_botoes.pack(pady=10)
        
        ttk.Button(frame_botoes, text="➕ Nova Sessão", command=self._nova_sessao, width=18).grid(row=0, column=0, padx=5, pady=3)
        ttk.Button(frame_botoes, text="✏️ Renomear", command=self._renomear_sessao, width=18).grid(row=0, column=1, padx=5, pady=3)
        ttk.Button(frame_botoes, text="📋 Duplicar", command=self._duplicar_sessao, width=18).grid(row=1, column=0, padx=5, pady=3)
        ttk.Button(frame_botoes, text="🗑 Excluir", command=self._excluir_sessao, width=18).grid(row=1, column=1, padx=5, pady=3)
        ttk.Button(frame_botoes, text="✓ Fechar", command=self._fechar, width=37).grid(row=2, column=0, columnspan=2, padx=5, pady=10)

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
        
        # Renomeia
        self.config['sessoes'][novo_nome] = self.config['sessoes'].pop(nome_antigo)
        
        # Atualiza sessão ativa se necessário
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
        
        # Duplica
        import copy
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
        
        # Se é a sessão ativa, muda para outra
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


# ==================== INTERFACE PRINCIPAL ====================

class MonitorApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Monitor de Arquivos")
        self.geometry("1080x720")
        self.resizable(False, False)
        self.configure(bg="#f2f2f2")

        # Carrega configuração completa
        self.config = carregar_config()
        self.sessao_atual = self.config['sessao_ativa']
        self.pastas = obter_pastas_sessao(self.config, self.sessao_atual)
        self.resultados = {}

        # Carrega últimas extensões usadas (persistidas em config)
        ult = self.config.get('ultimas_extensoes', {})
        self.ultimo_entrada = ult.get('entrada', 'rvt')
        self.ultimo_saida = ult.get('saida', 'ifc')

        self.filter_novos = tk.BooleanVar(value=True)
        self.filter_desatualizados = tk.BooleanVar(value=True)
        self.filter_atualizados = tk.BooleanVar(value=True)

        self._montar_interface()
        self._atualizar_lista_gui()
        
        # Mostra informação sobre o diretório Atlas ao iniciar
        self.log(f"📁 Configurações salvas em: {DIRETORIO_ATLAS}")
        self.log(f"📄 Arquivo: {os.path.basename(CONFIG_FILE)}\n")

    # ------------------------- INTERFACE ------------------------- #
    def _montar_interface(self):
        # Cabeçalho
        ttk.Label(
            self,
            text="🔄 Monitor de Atualizações de Arquivos",
            font=("Segoe UI", 16, "bold"),
            background="#f2f2f2",
        ).pack(pady=15)

        # Frame de sessão
        frame_sessao = ttk.Frame(self)
        frame_sessao.pack(pady=5)
        
        ttk.Label(frame_sessao, text="Sessão Ativa:", font=("Segoe UI", 10), background="#f2f2f2").pack(side="left", padx=5)
        
        self.combo_sessoes = ttk.Combobox(frame_sessao, width=30, state="readonly")
        self.combo_sessoes.pack(side="left", padx=5)
        self.combo_sessoes.bind("<<ComboboxSelected>>", self._trocar_sessao)
        self._atualizar_combo_sessoes()
        
        ttk.Button(frame_sessao, text="⚙️ Gerenciar Sessões", command=self._gerenciar_sessoes, width=20).pack(side="left", padx=5)

        # Botões principais
        frame_botoes = ttk.Frame(self)
        frame_botoes.pack(pady=10)

        ttk.Button(
            frame_botoes, text="📂 Adicionar Pasta(s)", width=25, command=self._adicionar_pastas
        ).grid(row=0, column=0, padx=10, pady=5)
        ttk.Button(
            frame_botoes, text="🗑 Remover Selecionada(s)", width=25, command=self._remover_pastas
        ).grid(row=0, column=1, padx=10, pady=5)
        ttk.Button(
            frame_botoes, text="🔍 Verificar Atualizações", width=25, command=self._verificar_atualizacoes
        ).grid(row=1, column=0, padx=10, pady=5)
        ttk.Button(
            frame_botoes, text="❌ Fechar", width=25, command=self.destroy
        ).grid(row=1, column=1, padx=10, pady=5)

        # Lista de pastas
        ttk.Label(
            self, text="Pastas Monitoradas:", font=("Segoe UI", 11, "bold"), background="#f2f2f2"
        ).pack(anchor="w", padx=20)

        self.lista_pastas = tk.Listbox(
            self, height=6, width=110, relief="groove", borderwidth=2, bg="#fafafa",
            selectmode=tk.EXTENDED
        )
        self.lista_pastas.pack(padx=20, pady=(0, 15))

        ttk.Label(
            self, text="Relatório:", font=("Segoe UI", 11, "bold"), background="#f2f2f2"
        ).pack(anchor="w", padx=10)

        # Container principal
        self.content_frame = ttk.Frame(self)
        self.content_frame.pack(fill="both", expand=True, padx=20, pady=(0, 10))

        # Frame do botão de filtro
        frame_filtro_relatorio = ttk.Frame(self.content_frame)
        frame_filtro_relatorio.pack(fill="x", padx=20, pady=(0,5), anchor="e")
        ttk.Button(frame_filtro_relatorio, text="🎛 Filtros", width=15, command=self._alternar_filtro_lateral).pack(side="right")

        # Log
        frame_log = ttk.Frame(self.content_frame, padding=10)
        frame_log.pack(side="left", fill="both", expand=True)

        self.log_box = scrolledtext.ScrolledText(
            frame_log,
            height=20,
            width=110,
            state="disabled",
            font=("Consolas", 9),
            relief="solid",
            borderwidth=1,
            background="#ffffff",
        )
        self.log_box.pack(fill="both", expand=True)

        # Frame lateral de filtros
        self.filtro_lateral = ttk.Frame(self.content_frame, width=200, relief="ridge")
        self.filtro_lateral.pack_propagate(False)
        self.filtro_visivel = False

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
        self.limpar_log()
        self.log(f"✓ Sessão alterada para: {nova_sessao}")
        self.log(f"📁 Configurações salvas em: {DIRETORIO_ATLAS}\n")

    def carregar_sessao_ativa(self):
        """Carrega as pastas da sessão ativa"""
        self.pastas = obter_pastas_sessao(self.config, self.sessao_atual)
        self._atualizar_lista_gui()
        self._atualizar_combo_sessoes()

    def _gerenciar_sessoes(self):
        """Abre janela de gerenciamento de sessões"""
        JanelaGerenciarSessoes(self, self.config)

    def _alternar_filtro_lateral(self):
        if self.filtro_visivel:
            self.filtro_lateral.pack_forget()
            self.filtro_visivel = False
        else:
            self.filtro_lateral.pack(side="right", fill="y", padx=(10, 0))
            self._montar_conteudo_filtro()
            self.filtro_visivel = True

    def _montar_conteudo_filtro(self):
        for widget in self.filtro_lateral.winfo_children():
            widget.destroy()

        ttk.Label(self.filtro_lateral, text="Filtros", font=("Segoe UI", 11, "bold")).pack(pady=(6, 8))

        ttk.Checkbutton(self.filtro_lateral, text="🆕 Novos", variable=self.filter_novos).pack(anchor="w", pady=2)
        ttk.Checkbutton(self.filtro_lateral, text="⚠️ Desatualizados", variable=self.filter_desatualizados).pack(anchor="w", pady=2)
        ttk.Checkbutton(self.filtro_lateral, text="✅ Atualizados", variable=self.filter_atualizados).pack(anchor="w", pady=2)

        ttk.Separator(self.filtro_lateral, orient="horizontal").pack(fill="x", pady=8)

        ttk.Button(self.filtro_lateral, text="Aplicar Filtro", width=18, command=self._aplicar_filtros).pack(pady=(0,6))
        ttk.Button(self.filtro_lateral, text="Limpar Filtros", width=18, command=self._limpar_filtros).pack(pady=(0,8))
        ttk.Button(self.filtro_lateral, text="Fechar", width=18, command=self._alternar_filtro_lateral).pack(pady=(0,10))

    # ------------------------- LOG ------------------------- #
    def log(self, msg: str):
        self.log_box.config(state="normal")
        self.log_box.insert("end", f"{msg}\n")
        self.log_box.see("end")
        self.log_box.config(state="disabled")

    def log_link(self, texto: str, caminho: str):
        self.log_box.config(state="normal")

        start_index = self.log_box.index("end-1c")
        self.log_box.insert("end", f"{texto}\n")
        end_index = self.log_box.index("end-1c")

        tag_name = f"link_{id(caminho)}_{datetime.now().timestamp()}"
        self.log_box.tag_add(tag_name, start_index, end_index)
        self.log_box.tag_config(tag_name, foreground="blue", underline=1)

        def abrir_pasta(event, path=caminho):
            try:
                path = os.path.normpath(path)
                if os.path.exists(path):
                    subprocess.run(['explorer', '/select,', path])
                else:
                    messagebox.showerror("Erro", f"Arquivo não encontrado:\n{path}")
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao abrir explorer:\n{str(e)}")

        self.log_box.tag_bind(tag_name, "<Button-1>", abrir_pasta)
        self.log_box.tag_bind(tag_name, "<Enter>", lambda e: self.log_box.config(cursor="hand2"))
        self.log_box.tag_bind(tag_name, "<Leave>", lambda e: self.log_box.config(cursor=""))

        self.log_box.see("end")
        self.log_box.config(state="disabled")

    def limpar_log(self):
        self.log_box.config(state="normal")
        self.log_box.delete(1.0, "end")
        self.log_box.config(state="disabled")

    def rodar_em_thread(self, func):
        threading.Thread(target=func, daemon=True).start()

    # ------------------------- CONFIGURAÇÃO ------------------------- #
    def _atualizar_lista_gui(self):
        self.lista_pastas.delete(0, "end")
        for p in self.pastas:
            self.lista_pastas.insert("end", f"{p['caminho']} ({p['entrada']} → {p['saida']})")
    
    def _configurar_extensoes_pasta(self, caminho):
        entrada_win = tk.Toplevel(self)
        entrada_win.title("Escolher Extensões")
        entrada_win.geometry("420x400")
        entrada_win.resizable(False, False)
        entrada_win.grab_set()
        entrada_win.transient(self)
        entrada_win.configure(bg="#f0f0f0")

        confirmado = [False]

        # Frame principal com padding
        main_frame = ttk.Frame(entrada_win, padding="20 15 20 20")
        main_frame.pack(fill="both", expand=True)

        # Cabeçalho
        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill="x", pady=(0, 15))

        ttk.Label(
            header_frame,
            text="📁 Configurar Extensões",
            font=("Segoe UI", 14, "bold"),
        ).pack(anchor="w")

        ttk.Separator(main_frame).pack(fill="x", pady=(0, 15))

        # Informações da pasta
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

        # Frame para as extensões
        ext_frame = ttk.Frame(main_frame)
        ext_frame.pack(fill="x", pady=(0, 20))

        # Entrada
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

        # Saída
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

        # Botões
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
            self._atualizar_lista_gui()
            self.log(f"📂 Pasta adicionada: {caminho} ({entrada_var.get()} → {saida_var.get()})")
            confirmado[0] = True
            entrada_win.destroy()

        ttk.Button(
            button_frame,
            text="✓ Confirmar",
            command=confirmar,
            style="Primary.TButton",
            width=15
        ).pack(side="right", padx=(0, 5))

        # Estilização dos botões
        style = ttk.Style()
        style.configure("Primary.TButton", background="#007bff", foreground="black")
        style.configure("Secondary.TButton", background="#6c757d")

        # Centraliza a janela
        entrada_win.update_idletasks()
        width = entrada_win.winfo_width()
        height = entrada_win.winfo_height()
        x = (entrada_win.winfo_screenwidth() // 2) - (width // 2)
        y = (entrada_win.winfo_screenheight() // 2) - (height // 2)
        entrada_win.geometry(f"{width}x{height}+{x}+{y}")

        self.wait_window(entrada_win)
        return confirmado[0]

# 👇 daqui pra baixo começa outro bloco, sem identação!



    def _remover_pastas(self):
        selecoes = self.lista_pastas.curselection()
        if not selecoes:
            messagebox.showinfo("Aviso", "Selecione uma ou mais pastas para remover.\n\nDica: Use Ctrl+Clique para selecionar múltiplas")
            return

        qtd = len(selecoes)
        if not messagebox.askyesno("Confirmar", f"Remover {qtd} pasta(s) selecionada(s)?"):
            return

        for idx in sorted(selecoes, reverse=True):
            pasta = self.pastas.pop(idx)
            self.log(f"🗑 Removida: {pasta['caminho']}")

        atualizar_pastas_sessao(self.config, self.sessao_atual, self.pastas)
        salvar_config(self.config)
        self._atualizar_lista_gui()
        messagebox.showinfo("Sucesso", f"{qtd} pasta(s) removida(s)")

    # ------------------------- FUNÇÕES DE FILTRO ------------------------- #
    def _aplicar_filtros(self):
        filtros = {
            'novos': self.filter_novos.get(),
            'desatualizados': self.filter_desatualizados.get(),
            'atualizados': self.filter_atualizados.get()
        }
        self._render_resultados_filtrados(self.resultados, filtros)

    def _limpar_filtros(self):
        self.filter_novos.set(True)
        self.filter_desatualizados.set(True)
        self.filter_atualizados.set(True)
        self._aplicar_filtros()

    def _render_resultados_filtrados(self, resultados, filtros):
        self.limpar_log()

        self.log("=" * 90)
        self.log("🔍 RELATÓRIO (FILTRADO)" if any(not v for v in filtros.values()) else "🔍 RELATÓRIO")
        self.log("=" * 90)
        self.log(f"Sessão: {self.sessao_atual}")
        self.log(f"Data/Hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        self.log(f"Pastas monitoradas: {len(self.pastas)}\n")

        if not resultados:
            self.log("Nenhum resultado disponível. Execute 'Verificar Atualizações' primeiro.")
            self.log("=" * 90)
            return

        total_novos = sum(len(r['novos']) for r in resultados.values())
        total_desatualizados = sum(len(r['desatualizados']) for r in resultados.values())
        total_atualizados = sum(len(r['atualizados']) for r in resultados.values())
        total_problemas = total_novos + total_desatualizados

        self.log("📊 RESUMO GERAL")
        self.log("-" * 90)
        self.log(f"🆕 Arquivos novos (precisam ser exportados): {total_novos}")
        self.log(f"⚠️  Arquivos desatualizados (precisam atualizar): {total_desatualizados}")
        self.log(f"✅ Arquivos atualizados: {total_atualizados}")
        self.log(f"📈 Total de ações necessárias: {total_problemas}\n")

        if total_problemas == 0 and not filtros['atualizados']:
            self.log("=" * 90)
            self.log("✅ TODAS AS PASTAS ESTÃO ATUALIZADAS!")
            self.log("=" * 90)
            return

        self.log("=" * 90)
        self.log("📂 DETALHAMENTO POR PASTA")
        self.log("=" * 90)

        shown_any = False
        for i, (caminho, resultado) in enumerate(resultados.items(), 1):
            config = resultado['config']
            novos = resultado['novos']
            desatualizados = resultado['desatualizados']
            atualizados = resultado['atualizados']

            mostrar_pasta = False
            if filtros['novos'] and novos:
                mostrar_pasta = True
            if filtros['desatualizados'] and desatualizados:
                mostrar_pasta = True
            if filtros['atualizados'] and atualizados:
                mostrar_pasta = True

            if not mostrar_pasta:
                continue

            shown_any = True
            self.log(f"\n[{i}] {caminho}")
            self.log(f"    Filtros: {config['entrada'].upper()} → {config['saida'].upper()}")
            self.log(f"    Status: {len(novos)} novo(s) | {len(desatualizados)} desatualizado(s)")

            if filtros['novos'] and novos:
                self.log(f"\n    🆕 ARQUIVOS NOVOS ({len(novos)}):")
                for item in novos:
                    self.log(f"       • {item['nome_base']}.{item['filtro_entrada']}")
                    self.log_link(f"         📥 Abrir arquivo", item['entrada']['caminho'])

            if filtros['desatualizados'] and desatualizados:
                self.log(f"\n    ⚠️  ARQUIVOS DESATUALIZADOS ({len(desatualizados)}):")
                for item in desatualizados:
                    self.log(f"       • {item['nome_base']} (desatualizado há {item['dias']} dias)")
                    self.log_link(f"         📥 Entrada ({item['filtro_entrada'].upper()}): {item['entrada']['data']}",
                                  item['entrada']['caminho'])
                    self.log_link(f"         📤 Saída ({item['filtro_saida'].upper()}): {item['saida']['data']}",
                                  item['saida']['caminho'])

            if filtros['atualizados'] and atualizados:
                self.log(f"\n    ✅ ARQUIVOS ATUALIZADOS ({len(atualizados)}):")
                for item in atualizados:
                    self.log(f"       • {item['nome_base']} ({item['entrada']['data']})")
                    self.log_link(f"         📥 Entrada ({item['entrada']['data']})", item['entrada']['caminho'])
                    self.log_link(f"         📤 Saída ({item['saida']['data']})", item['saida']['caminho'])

            self.log("")

        if not shown_any:
            self.log("\nNenhum item corresponde ao filtro selecionado.")
        self.log("=" * 90)
        self.log("✓ RELATÓRIO (FILTRADO) CONCLUÍDO")
        self.log("=" * 90)

    # ------------------------- MONITORAMENTO ------------------------- #
    def _verificar_atualizacoes(self):
        if not self.pastas:
            messagebox.showinfo("Aviso", "Nenhuma pasta configurada nesta sessão.")
            return

        def tarefa():
            self.limpar_log()
            self.log("=" * 90)
            self.log("🔍 VERIFICAÇÃO DE ATUALIZAÇÕES INICIADA")
            self.log("=" * 90)
            self.log(f"Sessão: {self.sessao_atual}")
            self.log(f"Data/Hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
            self.log(f"Pastas monitoradas: {len(self.pastas)}\n")

            self.resultados = verificar_atualizacoes(self.pastas)

            total_novos = sum(len(r['novos']) for r in self.resultados.values())
            total_desatualizados = sum(len(r['desatualizados']) for r in self.resultados.values())
            total_atualizados = sum(len(r['atualizados']) for r in self.resultados.values())
            total_problemas = total_novos + total_desatualizados

            self.log("📊 RESUMO GERAL")
            self.log("-" * 90)
            self.log(f"🆕 Arquivos novos (precisam ser exportados): {total_novos}")
            self.log(f"⚠️  Arquivos desatualizados (precisam atualizar): {total_desatualizados}")
            self.log(f"✅ Arquivos atualizados: {total_atualizados}")
            self.log(f"📈 Total de ações necessárias: {total_problemas}\n")

            if total_problemas == 0:
                self.log("=" * 90)
                self.log("✅ TODAS AS PASTAS ESTÃO ATUALIZADAS!")
                self.log("=" * 90)
                messagebox.showinfo("Resultado", "✅ Todos os arquivos estão atualizados!")
                return

            self.log("=" * 90)
            self.log("📂 DETALHAMENTO POR PASTA")
            self.log("=" * 90)

            for i, (caminho, resultado) in enumerate(self.resultados.items(), 1):
                config = resultado['config']
                novos = resultado['novos']
                desatualizados = resultado['desatualizados']
                atualizados = resultado['atualizados']

                if not novos and not desatualizados:
                    continue

                self.log(f"\n[{i}] {caminho}")
                self.log(f"    Filtros: {config['entrada'].upper()} → {config['saida'].upper()}")
                self.log(f"    Status: {len(novos)} novo(s) | {len(desatualizados)} desatualizado(s)")

                if novos:
                    self.log(f"\n    🆕 ARQUIVOS NOVOS ({len(novos)}):")
                    for item in novos:
                        self.log(f"       • {item['nome_base']}.{item['filtro_entrada']}")
                        self.log_link(f"         📥 Abrir arquivo", item['entrada']['caminho'])

                if desatualizados:
                    self.log(f"\n    ⚠️  ARQUIVOS DESATUALIZADOS ({len(desatualizados)}):")
                    for item in desatualizados:
                        self.log(f"       • {item['nome_base']} (desatualizado há {item['dias']} dias)")
                        self.log_link(f"         📥 Entrada ({item['filtro_entrada'].upper()}): {item['entrada']['data']}",
                                      item['entrada']['caminho'])
                        self.log_link(f"         📤 Saída ({item['filtro_saida'].upper()}): {item['saida']['data']}",
                                      item['saida']['caminho'])

                self.log("")

            self.log("=" * 90)
            self.log("✓ VERIFICAÇÃO CONCLUÍDA")
            self.log("=" * 90)

            resposta = messagebox.askyesno(
                "Verificação Concluída",
                f"🆕 Novos: {total_novos}\n⚠️ Desatualizados: {total_desatualizados}\n✅ Atualizados: {total_atualizados}\n\n"
                "Deseja gerar o relatório de arquivos agora?"
            )

            if resposta:
                destino = set.gerar_set(self.resultados)
                if destino:
                    self.log(f"\n📄 Lista de arquivos salva em: {destino}")
                    messagebox.showinfo("Relatório Gerado", f"Relatório salvo em:\n{destino}")

        self.rodar_em_thread(tarefa)

    # ------------------------- ADICIONAR PASTAS (MULTI) ------------------------- #
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

        # Para cada pasta selecionada, abre o diálogo de extensões (com padrões lembrados)
        for caminho in janela.pastas_selecionadas:
            # Se a pasta já estiver configurada, pula
            existe = any(p['caminho'] == caminho for p in self.pastas)
            if existe:
                self.log(f"⚠️ Pasta já configurada, pulando: {caminho}")
                continue

            confirmado = self._configurar_extensoes_pasta(caminho)
            # _configurar_extensoes_pasta já adiciona a pasta e salva config quando confirmada

if __name__ == "__main__":
    app = MonitorApp()
    app.mainloop()