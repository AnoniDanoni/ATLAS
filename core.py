# -*- coding: utf-8 -*-
# core.py - Lógica principal do ATLAS

import os
import json
import subprocess
import threading
import time
from datetime import datetime
from pathlib import Path


# ==================== CONFIGURAÇÃO DE DIRETÓRIO ====================

def obter_diretorio_atlas():
    """
    Retorna o caminho do diretório Atlas em AppData/Local. 
    Cria o diretório se não existir. 
    """
    appdata_local = os.getenv('LOCALAPPDATA')
    
    if appdata_local:
        diretorio_atlas = os.path.join(appdata_local, 'Atlas')
    else:
        diretorio_atlas = r'C:\Atlas'
    
    try:
        os.makedirs(diretorio_atlas, exist_ok=True)
        print(f"[INFO] Diretório Atlas: {diretorio_atlas}")
    except Exception as e:
        print(f"[ERRO] Não foi possível criar diretório Atlas: {e}")
        diretorio_atlas = os.getcwd()
    
    return diretorio_atlas


DIRETORIO_ATLAS = obter_diretorio_atlas()
CONFIG_FILE = os.path.join(DIRETORIO_ATLAS, "config_pastas.json")


# ==================== FUNÇÕES DE CONFIGURAÇÃO ====================

def carregar_config():
    """Carrega todas as sessões do arquivo de config"""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
                print(f"[INFO] Configuração carregada de: {CONFIG_FILE}")
                
                if 'arquivos_ignorados' not in config:
                    config['arquivos_ignorados'] = {}
                    print(f"[INFO] Estrutura 'arquivos_ignorados' adicionada")
                
                if 'relatorios_inaptid' not in config:
                    config['relatorios_inaptid'] = {}
                    print(f"[INFO] Estrutura 'relatorios_inaptid' adicionada")
                
                if 'status_arquivos' not in config:
                    config['status_arquivos'] = {}
                    print(f"[INFO] Estrutura 'status_arquivos' adicionada")
                
                return config
        except Exception as e:
            print(f"[ERRO] Erro ao carregar config: {e}")
    
    print(f"[INFO] Criando nova configuração padrão")
    return {
        'sessao_ativa': 'Padrão',
        'sessoes': {
            'Padrão': {
                'data_criacao': datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                'pastas': []
            }
        },
        'ultimas_extensoes': {
            'entrada': 'rvt',
            'saida': 'ifc'
        },
        'arquivos_ignorados': {},
        'relatorios_inaptid': {},
        'status_arquivos': {}
    }


def salvar_config(config_completo):
    """Salva toda a configuração incluindo todas as sessões"""
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config_completo, f, indent=2, ensure_ascii=False)
        print(f"[INFO] Configuração salva em: {CONFIG_FILE}")
    except Exception as e:
        print(f"[ERRO] Erro ao salvar config: {e}")
        from tkinter import messagebox
        messagebox.showerror("Erro", f"Não foi possível salvar configuração:\n{e}")


def obter_pastas_sessao(config, nome_sessao):
    """Retorna a lista de pastas de uma sessão específica, ordenadas alfabeticamente"""
    pastas = config['sessoes'].get(nome_sessao, {}).get('pastas', [])
    # Ordenar alfabeticamente por caminho (case-insensitive)
    return sorted(pastas, key=lambda p: p['caminho'].lower())


def atualizar_pastas_sessao(config, nome_sessao, pastas):
    """Atualiza as pastas de uma sessão específica"""
    if nome_sessao in config['sessoes']:
        config['sessoes'][nome_sessao]['pastas'] = pastas
        config['sessoes'][nome_sessao]['ultima_modificacao'] = datetime.now().strftime("%d/%m/%Y %H:%M:%S")


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
        
        for item in os.listdir(program_files):
            if item.startswith('Revit'):
                revit_path = os.path.join(program_files, item)
                
                if os.path.isdir(revit_path):
                    revit_exe = os.path.join(revit_path, 'Revit.exe')
                    
                    if os.path.exists(revit_exe):
                        versoes_encontradas.append((item, revit_exe))
                        print(f"[INFO] Revit detectado: {item} -> {revit_exe}")
        
        versoes_encontradas.sort(reverse=True)
        
    except Exception as e:
        print(f"[ERRO] Erro ao detectar Revit: {e}")
    
    return versoes_encontradas


def abrir_revit(revit_path):
    """
    Abre a aplicação Revit selecionada.
    Verifica se a MESMA versão do Revit já está em execução.
    
    Args:
        revit_path: Caminho completo do executável Revit.exe
    
    Returns:
        dict: {'sucesso': bool, 'ja_estava_aberto': bool}
    """
    from tkinter import messagebox
    
    try:
        if not os.path.exists(revit_path):
            messagebox.showerror("Erro", f"Revit não encontrado em:\n{revit_path}")
            return {'sucesso': False, 'ja_estava_aberto': False}
        
        versao_selecionada = os.path.dirname(revit_path).lower()
        print(f"[DEBUG] Versão selecionada: {versao_selecionada}")
        
        revit_ja_aberto = False
        mesma_versao = False
        
        try:
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
        
        if revit_ja_aberto and mesma_versao:
            print(f"[RESULTADO] Não reabrindo - mesma versão")
            return {'sucesso': True, 'ja_estava_aberto': True}
        
        print(f"[INFO] Abrindo Revit: {revit_path}")
        subprocess.Popen([revit_path])
        print(f"[INFO] Revit aberto com sucesso")
        
        return {'sucesso': True, 'ja_estava_aberto': False}
        
    except Exception as e:
        print(f"[ERRO] Erro ao abrir Revit: {e}")
        import traceback
        traceback.print_exc()
        messagebox.showerror("Erro", f"Erro ao abrir Revit:\n{str(e)}")
        return {'sucesso': False, 'ja_estava_aberto': False}


def executar_clover_rvt_para_nwc(revit_path, tempo_espera=75):
    """
    Executa a ação CLOVER > RVT para NWC no Revit após sua abertura.
    """
    try:
        import pyautogui
        
        versao = os.path.basename(os.path.dirname(revit_path))
        print(f"[INFO] Executando CLOVER para {versao}")
        
        if "2016" in versao:
            print(f"[INFO] Revit 2016 detectado - pulando execução de CLOVER")
            return
        
        print(f"[INFO] Aguardando {tempo_espera} segundos para o Revit inicializar...")
        for segundo in range(tempo_espera, 0, -1):
            barra = int((tempo_espera - segundo) / tempo_espera * 30)
            progresso = f"\r[{'█' * barra}{'░' * (30 - barra)}] {segundo}s restantes"
            print(progresso, end='', flush=True)
            time.sleep(1)
        
        print(f"\n[INFO] Tempo completo! Iniciando execução do CLOVER...")
        time.sleep(0.5)
        
        atlas_path = os.path.dirname(os.path.dirname(os.path.dirname(revit_path)))
        img_clover = os.path.join(atlas_path, "botoes", "clover.png")
        img_rvt_nwc = os.path.join(atlas_path, "botoes", "rvt_para_nwc.png")
        
        print(f"[DEBUG] Procurando imagem em: {img_clover}")
        print(f"[DEBUG] Procurando imagem em: {img_rvt_nwc}")
        
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


# ==================== FUNÇÕES DO MONITOR ====================

def extrair_nome_base(nome_arquivo, extensao_alvo):
    """Extrai o nome base de um arquivo, removendo todas as extensões"""
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
    """
    Escaneia uma pasta procurando por arquivos com extensão específica.
    Retorna dicionário com metadados dos arquivos encontrados.
    """
    arquivos = {}
    try:
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
        pass
    except FileNotFoundError:
        pass
    
    return arquivos


def verificar_atualizacoes(pastas_config):
    """
    Verifica atualizações de arquivos nas pastas configuradas.
    Compara timestamps de entrada e saída.
    """
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
