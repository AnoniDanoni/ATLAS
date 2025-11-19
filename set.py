import os
from tkinter import filedialog
import tkinter as tk

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