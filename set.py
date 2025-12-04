import os
from tkinter import filedialog
import tkinter as tk
import codecs
from collections import Counter

def analisar_formato_saida(resultados):
    """Analisa os formatos de saída dos arquivos desatualizados e novos
    
    Args:
        resultados: dicionário de resultados da verificação
    
    Returns:
        Tupla (formato_dominante, contador) onde formato_dominante é a extensão mais frequente
    """
    formatos = []
    
    for resultado in resultados.values():
        # Analisar novos
        for item in resultado['novos']:
            formato = item.get('filtro_saida', '').lower()
            if formato:
                formatos.append(formato)
        
        # Analisar desatualizados
        for item in resultado['desatualizados']:
            formato = item.get('filtro_saida', '').lower()
            if formato:
                formatos.append(formato)
    
    if not formatos:
        return (None, None)
    
    # Contar ocorrências
    contador = Counter(formatos)
    formato_dominante = contador.most_common(1)[0][0]  # Formato mais frequente
    
    return (formato_dominante, contador)

def gerar_command_temp(formato_saida, temp_folder=None):
    """Gera command_temp.txt baseado no formato de saída dominante
    
    Args:
        formato_saida: extensão/tipo do formato dominante (ex: 'nwc', 'ifc')
        temp_folder: pasta onde salvar. Se None, usa %TEMP% do Windows
    
    Returns:
        Caminho do arquivo criado ou None se formato inválido
    """
    # Mapeamento de formatos para comandos do Cloven
    comando_map = {
        'nwc': 'cloven-cloven-teste-autonwcexp',
        'ifc': 'cloven-cloven-teste-autoifcexp',  # Exemplo para IFC
        # Adicionar mais formatos conforme necessário
    }
    
    formato_norm = formato_saida.lower() if formato_saida else None
    comando = comando_map.get(formato_norm)
    
    if not comando:
        print(u"✖ Formato '{}' não mapeado para comando Cloven".format(formato_saida))
        return None
    
    # Definir pasta de destino
    if temp_folder is None:
        username = os.getenv('USERNAME')
        temp_folder = r'C:\Users\{}\AppData\Local\Temp'.format(username)
    
    # Garantir que a pasta existe
    if not os.path.exists(temp_folder):
        os.makedirs(temp_folder, exist_ok=True)
    
    command_file_path = os.path.join(temp_folder, 'comand_temp.txt')
    
    try:
        with codecs.open(command_file_path, 'w', 'utf-8') as f:
            f.write(comando + u'\n')
        print(u"✔ comand_temp.txt criado em: {}".format(command_file_path))
        return command_file_path
    except Exception as e:
        print(u"Erro ao criar comand_temp.txt: {}".format(str(e)))
        return None

def gerar_temp_set(resultados, temp_folder=None):
    """Gera temp_set.txt com arquivos novos e desatualizados (sem diálogo do usuário)
    e também gera command_temp.txt baseado no formato dominante
    
    Args:
        resultados: dicionário de resultados da verificação
        temp_folder: pasta onde salvar. Se None, usa %TEMP% do Windows
    
    Returns:
        Tupla (caminho_temp_set, caminho_command_temp) ou (None, None) se resultados vazios
    """
    arquivos = set()
    
    for resultado in resultados.values():
        for item in resultado['novos']:
            caminho_norm = os.path.normpath(item['entrada']['caminho'])
            arquivos.add(caminho_norm)
        for item in resultado['desatualizados']:
            caminho_norm = os.path.normpath(item['entrada']['caminho'])
            arquivos.add(caminho_norm)
    
    if not arquivos:
        return (None, None)
    
    # Definir pasta de destino
    if temp_folder is None:
        username = os.getenv('USERNAME')
        temp_folder = r'C:\Users\{}\AppData\Local\Temp'.format(username)
    
    # Garantir que a pasta existe
    if not os.path.exists(temp_folder):
        os.makedirs(temp_folder, exist_ok=True)
    
    temp_file_path = os.path.join(temp_folder, 'temp_set.txt')
    
    # Gerar temp_set.txt
    try:
        with codecs.open(temp_file_path, 'w', 'utf-8') as f:
            for caminho in sorted(arquivos):
                f.write(caminho + u'\n')
        print(u"✔ temp_set.txt criado em: {}".format(temp_file_path))
    except Exception as e:
        print(u"Erro ao criar temp_set.txt: {}".format(str(e)))
        return (None, None)
    
    # Analisar formato dominante e gerar command_temp.txt
    formato_dominante, contador = analisar_formato_saida(resultados)
    command_file_path = None
    
    if formato_dominante:
        print(u"📊 Análise de formatos: {}".format(dict(contador)))
        print(u"📌 Formato dominante: {}".format(formato_dominante))
        command_file_path = gerar_command_temp(formato_dominante, temp_folder)
    
    return (temp_file_path, command_file_path)

def gerar_set(resultados):
    """Extrai caminhos de arquivos novos e desatualizados dos resultados"""
    arquivos = set()
    
    for resultado in resultados.values():
        for item in resultado['novos']:
            # NORMALIZA o caminho para barras invertidas do Windows
            caminho_norm = os.path.normpath(item['entrada']['caminho'])
            arquivos.add(caminho_norm)
        for item in resultado['desatualizados']:
            # NORMALIZA o caminho para barras invertidas do Windows
            caminho_norm = os.path.normpath(item['entrada']['caminho'])
            arquivos.add(caminho_norm)
    
    if not arquivos:
        return None
    
    root = tk.Tk()
    root.withdraw()
    destino = filedialog.asksaveasfilename(
        title="Salvar lista de arquivos",
        defaultextension=".txt",
        filetypes=[("Text files", "*.txt")],
        initialfile="arquivos_para_processar.txt"
    )
    root.destroy()
    
    if destino:
        with open(destino, 'w', encoding='utf-8') as f:
            for caminho in sorted(arquivos):
                # Escreve o caminho já normalizado
                f.write(caminho + '\n')
        return destino
    return None