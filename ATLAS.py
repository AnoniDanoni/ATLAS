# -*- coding: utf-8 -*-
# monitor.py

import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext, messagebox, simpledialog
import threading
import subprocess
import os
import json
from datetime import datetime
from pathlib import Path
import set as set_module  # Renomeado para evitar conflito com o tipo set nativo
from loading_screen import tela_carregamento  

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


# ==================== FUNÇÕES DE DETECÇÃO REVIT ====================

def detectar_versoes_revit():
    """
    Detecta versões de Revit instaladas no sistema. 
    Procura em C:\\Program Files\\Autodesk\\
    Retorna lista de tuplas: [(nome_versao, caminho_executavel), ...]
    """
    versoes_encontradas = []
    
    try:
        program_files = os.path.join(os.environ.get('ProgramFiles', 'C:\\Program Files'), 'Autodesk')
        
        if not os.path.exists(program_files):
            print(f"[INFO] Diretório Autodesk não encontrado: {program_files}")
            return versoes_encontradas
        
        # Procura por pastas de Revit (Revit 2023, Revit 2024, etc.)
        for item in os.listdir(program_files):
            if item.startswith('Revit'):
                revit_path = os.path.join(program_files, item)
                
                if os.path.isdir(revit_path):
                    # Procura pelo executável Revit. exe
                    revit_exe = os.path.join(revit_path, 'Revit.exe')
                    
                    if os.path.exists(revit_exe):
                        versoes_encontradas.append((item, revit_exe))
                        print(f"[INFO] Revit detectado: {item} -> {revit_exe}")
        
        # Ordena por versão (mais recente primeiro)
        versoes_encontradas.sort(reverse=True)
        
    except Exception as e:
        print(f"[ERRO] Erro ao detectar Revit: {e}")
    
    return versoes_encontradas


def executar_clover_rvt_para_nwc(revit_path, tempo_espera=75):
    """
    Executa a ação CLOVER > RVT para NWC no Revit após sua abertura.
    Detecta os botões na tela usando template matching (busca de imagem).
    
    Args:
        revit_path: Caminho completo do executável Revit.exe
        tempo_espera: Tempo em segundos para aguardar antes de executar (padrão: 75 = 1min 15seg)
    """
    try:
        import pyautogui
        import time
        
        # Extrai a versão do Revit do caminho
        versao = os.path.basename(os.path.dirname(revit_path))
        print(f"[INFO] Executando CLOVER para {versao}")
        
        # Revit 2016 não tem suporte, pula a execução
        if "2016" in versao:
            print(f"[INFO] Revit 2016 detectado - pulando execução de CLOVER")
            return
        
        # Aguarda o tempo especificado com barra de progresso
        print(f"[INFO] Aguardando {tempo_espera} segundos para o Revit inicializar...")
        for segundo in range(tempo_espera, 0, -1):
            # Cria barra de progresso
            barra = int((tempo_espera - segundo) / tempo_espera * 30)  # 30 caracteres de barra
            progresso = f"\r[{'█' * barra}{'░' * (30 - barra)}] {segundo}s restantes"
            print(progresso, end='', flush=True)
            time.sleep(1)
        
        print(f"\n[INFO] Tempo completo! Iniciando execução do CLOVER...")
        time.sleep(0.5)
        
        # Caminho das imagens dos botões
        atlas_path = os.path.dirname(os.path.dirname(os.path.dirname(revit_path)))
        img_clover = os.path.join(atlas_path, "botoes", "clover.png")
        img_rvt_nwc = os.path.join(atlas_path, "botoes", "rvt_para_nwc.png")
        
        print(f"[DEBUG] Procurando imagem em: {img_clover}")
        print(f"[DEBUG] Procurando imagem em: {img_rvt_nwc}")
        
        # Procura pelo botão "CLOVER" usando template matching
        print(f"[INFO] Procurando botão CLOVER na tela...")
        try:
            clover_pos = pyautogui.locateOnScreen(img_clover, confidence=0.7)
            if clover_pos:
                print(f"[INFO] CLOVER encontrado em {clover_pos}, clicando...")
                pyautogui.click(clover_pos[0] + 30, clover_pos[1] + 15)
                time.sleep(1.5)
            else:
                print(f"[AVISO] Botão CLOVER não encontrado")
                print(f"[INFO] Verifique se o arquivo existe: {img_clover}")
                return
        except Exception as e:
            print(f"[ERRO] Erro ao procurar CLOVER: {e}")
            return
        
        # Procura pelo botão "RVT para NWC"
        print(f"[INFO] Procurando botão RVT para NWC na tela...")
        try:
            rvt_nwc_pos = pyautogui.locateOnScreen(img_rvt_nwc, confidence=0.7)
            if rvt_nwc_pos:
                print(f"[INFO] RVT para NWC encontrado em {rvt_nwc_pos}, clicando...")
                pyautogui.click(rvt_nwc_pos[0] + 30, rvt_nwc_pos[1] + 15)
                print(f"[INFO] ✓ CLOVER > RVT para NWC executado com sucesso!")
            else:
                print(f"[AVISO] Botão RVT para NWC não encontrado")
                print(f"[INFO] Verifique se o arquivo existe: {img_rvt_nwc}")
        except Exception as e:
            print(f"[ERRO] Erro ao procurar RVT para NWC: {e}")
            
    except ImportError:
        print(f"[AVISO] pyautogui não instalado")
        print(f"[AVISO] Instale com: pip install pyautogui")
    except Exception as e:
        print(f"[ERRO] Erro ao executar CLOVER: {e}")
        import traceback
        traceback.print_exc()


def abrir_revit(revit_path):
    """
    Abre a aplicação Revit selecionada.
    Verifica se a MESMA versão do Revit já está em execução.
    Se outra versão estiver aberta, abre a nova versão selecionada.
    
    Args:
        revit_path: Caminho completo do executável Revit.exe
    
    Returns:
        dict: {'sucesso': bool, 'ja_estava_aberto': bool}
    """
    try:
        if not os.path.exists(revit_path):
            messagebox.showerror("Erro", f"Revit não encontrado em:\n{revit_path}")
            return {'sucesso': False, 'ja_estava_aberto': False}
        
        # Extrai o diretório da versão selecionada
        versao_selecionada = os.path.dirname(revit_path).lower()
        print(f"[DEBUG] Versão selecionada: {versao_selecionada}")
        
        # Tenta usar PowerShell para obter o caminho exato do processo
        revit_ja_aberto = False
        mesma_versao = False
        
        try:
            # PowerShell command para obter o caminho do executável
            ps_command = 'Get-Process -Name Revit -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Path'
            ps_result = subprocess.run(
                ['powershell', '-Command', ps_command],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            print(f"[DEBUG] PowerShell output raw: '{ps_result.stdout}'")
            
            if ps_result.stdout.strip():
                for linha in ps_result.stdout.strip().split('\n'):
                    linha = linha.strip()
                    if linha and 'Revit.exe' in linha:
                        revit_ja_aberto = True
                        revit_aberto = os.path.dirname(linha).lower()
                        print(f"[DEBUG] Revit.exe aberto em: {revit_aberto}")
                        print(f"[DEBUG] Versão selecionada: {versao_selecionada}")
                        print(f"[DEBUG] Comparação: '{revit_aberto}' == '{versao_selecionada}' = {revit_aberto == versao_selecionada}")
                        
                        # Verifica se é a MESMA versão
                        if revit_aberto == versao_selecionada:
                            print(f"[INFO] Mesma versão de Revit já está em execução")
                            mesma_versao = True
                        else:
                            print(f"[INFO] Versão diferente encontrada, abrindo nova versão")
                        break
                        
        except subprocess.TimeoutExpired:
            print(f"[AVISO] Timeout ao executar PowerShell")
        except Exception as e:
            print(f"[AVISO] Erro ao executar PowerShell: {e}")
        
        # Se é a mesma versão, não reabre
        if revit_ja_aberto and mesma_versao:
            print(f"[RESULTADO] Não reabrindo - mesma versão")
            return {'sucesso': True, 'ja_estava_aberto': True}
        
        # Abre o Revit em um processo separado (nova versão ou nenhuma aberta)
        print(f"[INFO] Abrindo Revit: {revit_path}")
        subprocess.Popen([revit_path])
        print(f"[INFO] Revit aberto com sucesso")
        
        # Executa CLOVER em uma thread separada
        # thread_clover = threading.Thread(target=executar_clover_rvt_para_nwc, args=(revit_path,), daemon=True)
        # thread_clover.start()
        
        return {'sucesso': True, 'ja_estava_aberto': False}
        
    except Exception as e:
        print(f"[ERRO] Erro ao abrir Revit: {e}")
        import traceback
        traceback.print_exc()
        messagebox.showerror("Erro", f"Erro ao abrir Revit:\n{str(e)}")
        return {'sucesso': False, 'ja_estava_aberto': False}


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
        # Cabeçalho
        ttk.Label(
            self,
            text="🔧 Selecionar Revit",
            font=("Segoe UI", 10, "bold"),
            background="#5865F2"
        ).pack(pady=8, padx=10)
        
        # Instrução
        ttk.Label(
            self,
            text="Qual versão deseja usar?",
            font=("Segoe UI", 9),
            background="#5865F2"
        ).pack(pady=(0, 5))
        
        # Frame da lista
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
        
        # Preenche a listbox
        for nome_versao, _ in self.versoes:
            self.listbox.insert("end", nome_versao)
        
        # Seleciona a primeira (mais recente) por padrão
        if self.versoes:
            self.listbox.selection_set(0)
        
        # Frame de botões
        frame_botoes = ttk.Frame(self, padding="5")
        frame_botoes.pack(pady=8, fill="x", padx=15)
        
        # Frame interno para centralizar os botões
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


# ==================== FUNÇÕES DE CONFIGURAÇÃO COM SESSÕES ====================

def carregar_config():
    """Carrega todas as sessões do arquivo de config"""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
                print(f"[INFO] Configuração carregada de: {CONFIG_FILE}")
                
                # Migração: adiciona arquivos_ignorados se não existir
                if 'arquivos_ignorados' not in config:
                    config['arquivos_ignorados'] = {}
                    print(f"[INFO] Estrutura 'arquivos_ignorados' adicionada")
                
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
        # Adiciona aqui a persistência das últimas extensões usadas. 
        'ultimas_extensoes': {
            'entrada': 'rvt',
            'saida': 'ifc'
        },
        # Arquivos ignorados por pasta (caminho_pasta -> lista de nomes de arquivos)
        'arquivos_ignorados': {}
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

        # Cores do tema
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
        ttk.Label(self, text="Pastas Selecionadas:", font=("Segoe UI", 11, "bold"), background=self.bg_principal, foreground=self.fg_texto).pack(pady=10, padx=10, anchor="w")
        
        # Frame da lista com borda
        frame_lista_border = tk.Frame(self, bg=self.cor_acento)
        frame_lista_border.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        frame_lista = tk.Frame(frame_lista_border, bg=self.bg_principal)
        frame_lista.pack(fill="both", expand=True, padx=2, pady=2)

        scrollbar = ttk.Scrollbar(frame_lista)
        scrollbar.pack(side="right", fill="y")

        self.listbox = tk.Listbox(frame_lista, height=15, yscrollcommand=scrollbar.set, relief="flat", borderwidth=0, 
                                   bg=self.bg_terciario, fg=self.fg_texto, selectbackground=self.cor_acento, 
                                   selectforeground="#ffffff", font=("Segoe UI", 9))
        self.listbox.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=self.listbox.yview)

        frame_botoes = tk.Frame(self, bg=self.bg_principal)
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
        
        # Cores do tema
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
        # Cabeçalho
        header_frame = tk.Frame(self, bg=self.bg_secundario)
        header_frame.pack(fill="x", pady=(0, 10))
        
        ttk.Label(header_frame, text="📋 Sessões Configuradas", font=("Segoe UI", 12, "bold"), background=self.bg_secundario, foreground=self.cor_acento).pack(pady=10)
        
        # Frame da lista com borda
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
        
        # Frame de botões
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
        self.title("ATLAS")
        self.geometry("1080x720")
        self.resizable(False, False)
        
        # Tema Discord (Cinza Discord com roxo acentuado)
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
        
        # Configurar tema ttk
        self._configurar_estilo_ttk()

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
        
        # Flag para controlar se estamos visualizando ignorados
        self.visualizando_ignorados = False

        self._montar_interface()
        self._atualizar_lista_gui()
        
        # Mostra informação sobre o diretório Atlas ao iniciar
        self.log(f"📁 Configurações salvas em: {DIRETORIO_ATLAS}")
        self.log(f"📄 Arquivo: {os.path.basename(CONFIG_FILE)}\n")
    
    def _configurar_estilo_ttk(self):
        """Configura o estilo visual dos widgets ttk"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Fundo e texto padrão
        style.configure('TLabel', background=self.bg_principal, foreground=self.fg_texto)
        style.configure('TFrame', background=self.bg_principal)
        style.configure('TButton', background=self.bg_terciario, foreground=self.fg_texto, 
                       borderwidth=1, focuscolor='none', padding=6)
        style.map('TButton', 
                 background=[('active', self.cor_acento), ('pressed', self.cor_acento)],
                 foreground=[('active', '#ffffff'), ('pressed', '#ffffff')])
        
        # Combobox
        style.configure('TCombobox', fieldbackground="#5865F2", background="#5865F2",
                       foreground=self.fg_texto)
        style.map('TCombobox', fieldbackground=[('readonly', '#5865F2'), ('active', '#5865F2')])
        
        # Checkbutton
        style.configure('TCheckbutton', background=self.bg_principal, foreground=self.fg_texto)
        style.map('TCheckbutton', background=[('active', self.bg_principal)])

    # ------------------------- INTERFACE ------------------------- #
    def _montar_interface(self):
        # Cabeçalho com fundo destaque
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

        # Frame de sessão
        frame_sessao = tk.Frame(self, bg=self.bg_principal)
        frame_sessao.pack(pady=8)
        
        ttk.Label(frame_sessao, text="Sessão Ativa:", font=("Segoe UI", 10, "bold"), background=self.bg_principal, foreground=self.fg_texto).pack(side="left", padx=5)
        
        self.combo_sessoes = ttk.Combobox(frame_sessao, width=30, state="readonly")
        self.combo_sessoes.pack(side="left", padx=5)
        self.combo_sessoes.bind("<<ComboboxSelected>>", self._trocar_sessao)
        self._atualizar_combo_sessoes()
        
        ttk.Button(frame_sessao, text="⚙️ Gerenciar Sessões", command=self._gerenciar_sessoes, width=20).pack(side="left", padx=5)
        
        # Botões principais com frame destacado
        frame_botoes = tk.Frame(self, bg=self.bg_principal)
        frame_botoes.pack(pady=8)

        ttk.Button(
            frame_botoes, text="📂 Adicionar Pasta(s)", width=25, command=self._adicionar_pastas
        ).grid(row=0, column=0, padx=8, pady=4)
        ttk.Button(
            frame_botoes, text="🗑 Remover Selecionada(s)", width=25, command=self._remover_pastas
        ).grid(row=0, column=1, padx=8, pady=4)
        ttk.Button(
            frame_botoes, text="🔍 Verificar Atualizações", width=25, command=self._verificar_atualizacoes
        ).grid(row=1, column=0, padx=8, pady=4)
        ttk.Button(
            frame_botoes, text="❌ Fechar", width=25, command=self.destroy
        ).grid(row=1, column=1, padx=8, pady=4)

        # Lista de pastas com borda melhorada
        ttk.Label(
            self, text="Pastas Monitoradas:", font=("Segoe UI", 11, "bold"), background=self.bg_principal, foreground=self.fg_texto
        ).pack(anchor="w", padx=20, pady=(10, 3))

        # Frame para listbox com borda (roxo muito desbotado)
        frame_lista = tk.Frame(self, bg="#3D3F5C", highlightthickness=0)
        frame_lista.pack(padx=20, pady=(0, 12), fill="both")
        
        self.lista_pastas = tk.Listbox(
            frame_lista, height=5, width=110, relief="flat", borderwidth=0, bg=self.bg_terciario,
            selectmode=tk.EXTENDED, fg=self.fg_texto, selectbackground=self.cor_acento,
            selectforeground="#ffffff", font=("Segoe UI", 9)
        )
        self.lista_pastas.pack(padx=2, pady=2, fill="both", expand=True)

        ttk.Label(
            self, text="Relatório:", font=("Segoe UI", 11, "bold"), background=self.bg_principal, foreground=self.fg_texto
        ).pack(anchor="w", padx=20, pady=(5, 3))

        # Container principal
        self.content_frame = tk.Frame(self, bg=self.bg_principal)
        self.content_frame.pack(fill="both", expand=True, padx=20, pady=(0, 10))

        # Frame do botão de filtro
        frame_filtro_relatorio = tk.Frame(self.content_frame, bg=self.bg_principal)
        frame_filtro_relatorio.pack(fill="x", padx=0, pady=(0, 8))
        self.btn_ignorados = ttk.Button(frame_filtro_relatorio, text="📋 Ignorados", width=15, command=self._mostrar_ignorados)
        self.btn_ignorados.pack(side="left", padx=2)
        ttk.Button(frame_filtro_relatorio, text="🎛 Filtros", width=15, command=self._alternar_filtro_lateral).pack(side="right", padx=2)
        ttk.Button(frame_filtro_relatorio, text="🔄 Reverter Ignorados", width=18, command=self._reverter_ignorados).pack(side="right", padx=2)
        ttk.Button(frame_filtro_relatorio, text="🚫 Ignorar Arquivos", width=18, command=self._ignorar_arquivos).pack(side="right", padx=2)

        # Log com borda (roxo muito desbotado)
        frame_log = tk.Frame(self.content_frame, bg="#5A5E93", highlightthickness=0)
        frame_log.pack(side="left", fill="both", expand=True, padx=0)

        self.log_box = scrolledtext.ScrolledText(
            frame_log,
            height=20,
            width=110,
            state="disabled",
            font=("Consolas", 9),
            relief="flat",
            borderwidth=0,
            background=self.bg_secundario,
            foreground=self.fg_texto,
            insertbackground=self.fg_texto,
        )
        self.log_box.pack(fill="both", expand=True, padx=2, pady=2)

        # Frame lateral de filtros
        self.filtro_lateral = tk.Frame(self.content_frame, width=200, bg=self.bg_terciario, relief="solid", bd=1)
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
        JanelaGerenciarSessoes(self, self.config, self.bg_principal, self.bg_secundario, self.fg_texto, self.fg_texto_secundario)

    def _alternar_filtro_lateral(self):
        if self.filtro_visivel:
            self.filtro_lateral.pack_forget()
            self.filtro_visivel = False
        else:
            self.filtro_lateral.pack(side="right", fill="y", padx=(10, 0))
            self._montar_conteudo_filtro()
            self. filtro_visivel = True

    def _montar_conteudo_filtro(self):
        for widget in self.filtro_lateral.winfo_children():
            widget.destroy()

        ttk.Label(self.filtro_lateral, text="Filtros", font=("Segoe UI", 11, "bold"), background=self.bg_terciario, foreground=self.cor_acento).pack(pady=(8, 12), padx=8)

        ttk.Checkbutton(self.filtro_lateral, text="🆕 Novos", variable=self.filter_novos).pack(anchor="w", pady=4, padx=8)
        ttk.Checkbutton(self.filtro_lateral, text="⚠️ Desatualizados", variable=self.filter_desatualizados).pack(anchor="w", pady=4, padx=8)
        ttk.Checkbutton(self.filtro_lateral, text="✅ Atualizados", variable=self.filter_atualizados).pack(anchor="w", pady=4, padx=8)

        ttk.Separator(self.filtro_lateral, orient="horizontal").pack(fill="x", pady=10, padx=8)

        ttk.Button(self.filtro_lateral, text="Aplicar Filtro", width=16, command=self._aplicar_filtros).pack(pady=(0,6), padx=8)
        ttk.Button(self.filtro_lateral, text="Limpar Filtros", width=16, command=self._limpar_filtros).pack(pady=(0,8), padx=8)
        ttk.Button(self.filtro_lateral, text="Fechar", width=16, command=self._alternar_filtro_lateral).pack(pady=(0,10), padx=8)

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
        self.log_box.tag_config(tag_name, foreground="#43B581", underline=1)

        def abrir_pasta(event, path=caminho):
            try:
                path = os.path.normpath(path)
                if os.path.exists(path):
                    subprocess.run(['explorer', '/select,', path])
                else:
                    messagebox.showerror("Erro", f"Arquivo não encontrado:\n{path}")
            except Exception as e:
                messagebox. showerror("Erro", f"Erro ao abrir explorer:\n{str(e)}")

        self.log_box. tag_bind(tag_name, "<Button-1>", abrir_pasta)
        self.log_box.tag_bind(tag_name, "<Enter>", lambda e: self.log_box.config(cursor="hand2"))
        self. log_box.tag_bind(tag_name, "<Leave>", lambda e: self.log_box.config(cursor=""))

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
        entrada_win = tk. Toplevel(self)
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
            self.log(f"📂 Pasta adicionada: {caminho} ({entrada_var.get()} → {saida_var. get()})")
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

    def _remover_pastas(self):
        selecoes = self.lista_pastas.curselection()
        if not selecoes:
            messagebox.showinfo("Aviso", "Selecione uma ou mais pastas para remover.\n\nDica: Use Ctrl+Clique para selecionar múltiplas")
            return

        qtd = len(selecoes)
        if not messagebox.askyesno("Confirmar", f"Remover {qtd} pasta(s) selecionada(s)? "):
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
        self.filter_novos. set(True)
        self.filter_desatualizados.set(True)
        self.filter_atualizados.set(True)
        self._aplicar_filtros()

    def _ignorar_arquivos(self):
        """Permite selecionar arquivos para ignorar da pasta selecionada"""
        try:
            selecionadas = self.lista_pastas.curselection()
            
            if not selecionadas:
                messagebox.showwarning("Aviso", "Selecione uma pasta monitorada")
                return
            
            if len(selecionadas) > 1:
                messagebox.showwarning("Aviso", "Selecione apenas uma pasta por vez")
                return
            
            # Pega o caminho da pasta selecionada
            idx = selecionadas[0]
            pasta_info = self.pastas[idx]
            caminho_pasta = pasta_info['caminho']
            
            # Abre diálogo de seleção de arquivos
            from tkinter import filedialog
            
            arquivos_selecionados = filedialog.askopenfilenames(
                title="Selecione arquivos para ignorar",
                initialdir=caminho_pasta,
                filetypes=[
                    ("Arquivos suportados", "*.rvt *.dwg *.ifc *.nwc"),
                    ("Revit", "*.rvt"),
                    ("AutoCAD", "*.dwg"),
                    ("IFC", "*.ifc"),
                    ("Navisworks", "*.nwc"),
                    ("Todos", "*.*")
                ]
            )
            
            if not arquivos_selecionados:
                return
            
            # Inicializa estrutura se não existir
            if 'arquivos_ignorados' not in self.config:
                self.config['arquivos_ignorados'] = {}
            
            if caminho_pasta not in self.config['arquivos_ignorados']:
                self.config['arquivos_ignorados'][caminho_pasta] = []
            
            # Extrai apenas os nomes dos arquivos
            ignorados = set(self.config['arquivos_ignorados'][caminho_pasta])
            adicionados = 0
            
            for caminho_arquivo in arquivos_selecionados:
                nome_arquivo = os.path.basename(caminho_arquivo)
                if nome_arquivo not in ignorados:
                    ignorados.add(nome_arquivo)
                    adicionados += 1
            
            # Salva configuração
            self.config['arquivos_ignorados'][caminho_pasta] = list(ignorados)
            salvar_config(self.config)
            
            if adicionados > 0:
                messagebox.showinfo("Sucesso", f"{adicionados} arquivo(s) adicionado(s) à lista de ignorados")
            else:
                messagebox.showinfo("Info", "Arquivo(s) já estavam na lista de ignorados")
        
        except Exception as e:
            messagebox.showerror("Erro", f"Erro:\n{str(e)}")
            import traceback
            traceback.print_exc()

    def _reverter_ignorados(self):
        """Remove todos os arquivos ignorados da pasta selecionada"""
        try:
            selecionadas = self.lista_pastas.curselection()
            
            if not selecionadas:
                messagebox.showwarning("Aviso", "Selecione uma pasta monitorada")
                return
            
            # Pega o caminho da pasta selecionada
            idx = selecionadas[0]
            pasta_info = self.pastas[idx]
            caminho_pasta = pasta_info['caminho']
            
            # Verifica se há ignorados
            if 'arquivos_ignorados' not in self.config or caminho_pasta not in self.config['arquivos_ignorados']:
                messagebox.showinfo("Info", "Nenhum arquivo ignorado nesta pasta")
                return
            
            ignorados = self.config['arquivos_ignorados'][caminho_pasta]
            if not ignorados:
                messagebox.showinfo("Info", "Nenhum arquivo ignorado nesta pasta")
                return
            
            # Confirma remoção
            qtd = len(ignorados)
            if not messagebox.askyesno("Confirmar", f"Remover {qtd} arquivo(s) da lista de ignorados?\n\n{chr(10).join(ignorados[:5])}{'...' if qtd > 5 else ''}"):
                return
            
            # Remove ignorados
            self.config['arquivos_ignorados'][caminho_pasta] = []
            salvar_config(self.config)
            messagebox.showinfo("Sucesso", f"{qtd} arquivo(s) removido(s) da lista de ignorados")
        
        except Exception as e:
            messagebox.showerror("Erro", f"Erro:\n{str(e)}")
            import traceback
            traceback.print_exc()

    def _mostrar_ignorados(self):
        """Mostra a lista de arquivos ignorados no log ou volta ao log de resultados"""
        try:
            # Se já está visualizando ignorados, volta ao log de resultados
            if self.visualizando_ignorados:
                self.visualizando_ignorados = False
                self.btn_ignorados.config(text="📋 Ignorados")
                # Volta ao log de resultados se houver
                if self.resultados:
                    filtros = {
                        'novos': self.filter_novos.get(),
                        'desatualizados': self.filter_desatualizados.get(),
                        'atualizados': self.filter_atualizados.get()
                    }
                    self._render_resultados_filtrados(self.resultados, filtros)
                else:
                    self.limpar_log()
                    self.log("ℹ️  Execute 'Verificar Atualizações' primeiro para ver resultados")
                return
            
            # Marca que estamos visualizando ignorados
            self.visualizando_ignorados = True
            self.btn_ignorados.config(text="📋 Relatório")
            
            # Limpa o log
            self.limpar_log()
            
            # Verifica se há arquivos ignorados
            if 'arquivos_ignorados' not in self.config or not self.config['arquivos_ignorados']:
                self.log("ℹ️  Nenhum arquivo ignorado registrado")
                return
            
            self.log("=" * 80)
            self.log("📋 LISTA DE ARQUIVOS IGNORADOS")
            self.log("=" * 80)
            
            total_ignorados = 0
            
            # Itera sobre todas as pastas
            for caminho_pasta, arquivos in self.config['arquivos_ignorados'].items():
                if arquivos:
                    self.log(f"\n📁 Pasta: {caminho_pasta}")
                    self.log("-" * 80)
                    
                    for i, arquivo in enumerate(arquivos, 1):
                        self.log(f"  {i:3d}. {arquivo}")
                    
                    self.log(f"\n  Subtotal: {len(arquivos)} arquivo(s) ignorado(s)\n")
                    total_ignorados += len(arquivos)
            
            self.log("=" * 80)
            self.log(f"✓ Total de arquivos ignorados: {total_ignorados}")
            self.log("=" * 80)
        
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao exibir ignorados:\n{str(e)}")
            import traceback
            traceback.print_exc()

    def _filtrar_ignorados(self, resultados):
        """Filtra resultados removendo arquivos ignorados"""
        if 'arquivos_ignorados' not in self.config:
            return resultados
        
        resultados_filtrados = {}
        for caminho_pasta, resultado in resultados.items():
            ignorados = set(self.config['arquivos_ignorados'].get(caminho_pasta, []))
            
            # Filtra cada categoria
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
        
        # Verifica nome_base direto
        if nome_base in ignorados:
            return True
        
        # Verifica arquivo de entrada
        info_entrada = arquivo_info.get('entrada', {})
        if info_entrada:
            arquivo_entrada = info_entrada.get('arquivo', '')
            if arquivo_entrada in ignorados:
                return True
        
        # Verifica se algum ignorado começa com o mesmo nome base
        nome_sem_ext = nome_base.rsplit('.', 1)[0] if '.' in nome_base else nome_base
        for ignorado in ignorados:
            ignorado_sem_ext = ignorado.rsplit('.', 1)[0] if '.' in ignorado else ignorado
            if nome_sem_ext == ignorado_sem_ext:
                return True
        
        return False

    def _render_resultados_filtrados(self, resultados, filtros):
        self.limpar_log()

        self.log("=" * 90)
        self.log("🔍 RELATÓRIO (FILTRADO)" if any(not v for v in filtros.values()) else "🔍 RELATÓRIO")
        self.log("=" * 90)
        self.log(f"Sessão: {self.sessao_atual}")
        self.log(f"Data/Hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        self.log(f"Pastas monitoradas: {len(self.pastas)}\n")

        if not resultados:
            self.log("Nenhum resultado disponível.  Execute 'Verificar Atualizações' primeiro.")
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
            # Reset da flag de visualização de ignorados
            self.visualizando_ignorados = False
            self.btn_ignorados.config(text="📋 Ignorados")
            
            self.limpar_log()
            self.log("=" * 90)
            self.log("🔍 VERIFICAÇÃO DE ATUALIZAÇÕES INICIADA")
            self.log("=" * 90)
            self.log(f"Sessão: {self.sessao_atual}")
            self.log(f"Data/Hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
            self.log(f"Pastas monitoradas: {len(self.pastas)}\n")

            # Executa verificação de atualizações
            self.resultados = verificar_atualizacoes(self.pastas)
            
            # Filtra arquivos ignorados
            self.resultados = self._filtrar_ignorados(self.resultados)

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

            # Dialog personalizado com 3 botões (Dark Theme)
            dialog = tk.Toplevel(self)
            dialog.title("Verificação Concluída")
            dialog.geometry("280x160")
            dialog.resizable(False, False)
            dialog.grab_set()
            dialog.transient(self)
            dialog.configure(bg=self.bg_principal)
            
            # Ícone/Header
            header_frame = tk.Frame(dialog, bg=self.bg_principal)
            header_frame.pack(pady=5, padx=15)
            
            tk.Label(
                header_frame,
                text="✓ Verificação Concluída",
                font=("Segoe UI", 10, "bold"),
                background=self.bg_principal,
                foreground=self.cor_acento
            ).pack(anchor="w")
            
            # Informações
            info_frame = tk.Frame(dialog, bg=self.bg_principal)
            info_frame.pack(pady=(0, 5), padx=15, fill="both", expand=True)
            
            tk.Label(
                info_frame,
                text="Resultados da Verificação:",
                font=("Segoe UI", 8),
                background=self.bg_principal,
                foreground=self.fg_texto
            ).pack(anchor="center", pady=(0, 2))
            
            tk.Label(
                info_frame,
                text=f"🆕 Novos: {total_novos}",
                font=("Segoe UI", 9),
                background=self.bg_principal,
                foreground=self.fg_texto
            ).pack(anchor="center", pady=0)
            
            
            tk.Label(
                info_frame,
                text=f"⚠️ Desatualizados: {total_desatualizados}",
                font=("Segoe UI", 9),
                background=self.bg_principal,
                foreground=self.fg_texto
            ).pack(anchor="center", pady=0)
            
            tk.Label(
                info_frame,
                text=f"✅ Atualizados: {total_atualizados}",
                font=("Segoe UI", 9),
                background=self.bg_principal,
                foreground=self.fg_texto
            ).pack(anchor="center", pady=0)
            
            # Frame de botões
            button_frame = tk.Frame(dialog, bg=self.bg_principal)
            button_frame.pack(pady=5, fill="x", padx=15)
            
            # Frame interno para centralizar os botões
            buttons_inner = tk.Frame(button_frame, bg=self.bg_principal)
            buttons_inner.pack(anchor="center")
            
            def atualizar():
                dialog.destroy()
                
                # Gera temp_set.txt com os arquivos novos e desatualizados
                # E também gera command_temp.txt baseado no formato dominante
                self.log("\n📝 Gerando temp_set.txt e analisando formatos...")
                temp_file, command_file = set_module.gerar_temp_set(self.resultados)
                
                if temp_file:
                    self.log(f"✓ temp_set.txt criado em: {temp_file}")
                else:
                    self.log("⚠️  Nenhum arquivo para atualizar (temp_set.txt não foi criado)")
                    messagebox.showwarning("Aviso", "Nenhum arquivo novo ou desatualizado para processar.")
                    return
                
                if command_file:
                    self.log(f"✓ command_temp.txt criado em: {command_file}")
                else:
                    self.log("⚠️  Nenhum comando foi definido para o formato dominante.")
                
                # Detecta versões Revit disponíveis
                versoes_revit = detectar_versoes_revit()
                
                if not versoes_revit:
                    self.log("\n❌ ERRO: Nenhuma versão de Revit foi detectada no sistema.")
                    self.log("\nVerifique se o Revit está instalado em:")
                    self.log(f"   {os.path.join(os.environ.get('ProgramFiles', 'C:\\Program Files'), 'Autodesk')}")
                    messagebox.showerror("Revit Não Encontrado", "Nenhuma versão de Revit foi detectada no sistema.")
                    return
                
                # Abre dialog de seleção de Revit
                janela_revit = JanelaSelecaoRevit(self, versoes_revit)
                self.wait_window(janela_revit)
                
                if not janela_revit.revit_selecionado:
                    self.log("\n⚠️ Operação cancelada. Nenhuma versão de Revit foi selecionada.")
                    return
                
                nome_revit, caminho_revit = janela_revit.revit_selecionado
                
                self.log(f"\n" + "=" * 90)
                self.log(f"Revit Selecionado: {nome_revit}")
                self.log("=" * 90)
                
                # Abre Revit
                self.log(f"🚀 Abrindo {nome_revit}...")
                
                # Mostra tela de carregamento
                tela = tela_carregamento(
                    titulo="Carregando Revit",
                    mensagem=f"Abrindo {nome_revit}...",
                    duracao=60,
                    parent=self
                )
                
                resultado_abertura = abrir_revit(caminho_revit)
                
                if resultado_abertura['sucesso']:
                    if resultado_abertura['ja_estava_aberto']:
                        self.log(f"⚠️  {nome_revit} já estava aberto! Usando a instância existente...")
                    else:
                        self.log(f"✓ {nome_revit} aberto com sucesso!")
                else:
                    self.log(f"❌ Erro ao abrir {nome_revit}")
            
            def gerar_relatorio():
                dialog.destroy()
                destino = set_module.gerar_set(self.resultados, parent=self)
                if destino:
                    self.log(f"\n📄 Lista de arquivos salva em: {destino}")
                    messagebox.showinfo("Relatório Gerado", f"Relatório salvo em:\n{destino}")
            
            def fechar():
                dialog.destroy()
            
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
                text="Fechar",
                command=fechar,
                width=11
            ).pack(side="left", padx=2)
            
            self.wait_window(dialog)

        self.rodar_em_thread(tarefa)

    # ------------------------- ADICIONAR PASTAS (MULTI) ------------------------- #
    def _adicionar_pastas(self):
        """
        Abre a janela de seleção múltipla.  Para cada pasta confirmada,
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
