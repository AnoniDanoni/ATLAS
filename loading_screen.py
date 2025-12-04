# -*- coding: utf-8 -*-
# loading_screen.py

import tkinter as tk
from tkinter import ttk
import threading
import time


def tela_carregamento(titulo="Carregando", mensagem="Por favor, aguarde...", duracao=60, parent=None):
    """
    Cria uma tela de carregamento com barra de progresso.
    
    Args:
        titulo (str): Título da janela
        mensagem (str): Mensagem a exibir
        duracao (int): Duração em segundos (padrão: 60)
        parent (tk.Tk): Janela pai (opcional)
    
    Returns:
        tk.Toplevel: A janela de carregamento criada
    
    Exemplo de uso:
        from loading_screen import tela_carregamento
        
        # Uso simples
        tela = tela_carregamento()
        
        # Uso customizado
        tela = tela_carregamento(
            titulo="Abrindo Revit",
            mensagem="Inicializando aplicação...",
            duracao=45,
            parent=root
        )
    """
    
    # Cria a janela
    janela = tk.Toplevel(parent) if parent else tk.Toplevel()
    janela.title(titulo)
    janela.geometry("380x160")
    janela.resizable(False, False)
    janela.configure(bg="#000000")
    
    # Remove bordas
    janela.overrideredirect(True)
    
    # Desabilita o botão de fechar
    janela.protocol("WM_DELETE_WINDOW", lambda: None)
    
    # Força a janela ficar sempre acima de todas
    janela.attributes('-topmost', True)
    
    # Se houver janela pai, coloca em cima
    if parent:
        janela.transient(parent)
    
    janela.lift()
    janela.focus_force()
    
    # Centraliza a janela
    janela.update_idletasks()
    largura = janela.winfo_width()
    altura = janela.winfo_height()
    tela_width = janela.winfo_screenwidth()
    tela_height = janela.winfo_screenheight()
    
    pos_x = (tela_width // 2) - (largura // 2)
    pos_y = (tela_height // 2) - (altura // 2)
    janela.geometry(f"+{pos_x}+{pos_y}")
    
    # Frame principal
    frame_principal = tk.Frame(janela, bg="#000000")
    frame_principal.pack(fill="both", expand=True, padx=20, pady=15)
    
    # Título com ícone - CENTRALIZADO
    label_titulo = tk.Label(
        frame_principal,
        text="⟳ " + titulo,
        font=("Segoe UI", 12, "bold"),
        background="#000000",
        foreground="#ffffff"
    )
    label_titulo.pack(pady=(0, 8), expand=True)
    
    # Mensagem (opcional) - CENTRALIZADA
    if mensagem:
        label_mensagem = tk.Label(
            frame_principal,
            text=mensagem,
            font=("Segoe UI", 10),
            background="#000000",
            foreground="#e0e0e0"
        )
        label_mensagem.pack(pady=(0, 12), expand=True)
    
    # Barra de progresso com estilo melhorado
    style = ttk.Style()
    style.theme_use('clam')
    style.configure(
        "custom.Horizontal.TProgressbar",
        background="#1a63bc",
        troughcolor="#333333",
        bordercolor="#000000",
        lightcolor="#1a63bc",
        darkcolor="#1a63bc"
    )
    
    progress = ttk.Progressbar(
        frame_principal,
        length=320,
        mode="determinate",
        maximum=100,
        value=0,
        style="custom.Horizontal.TProgressbar"
    )
    progress.pack(pady=0, fill="x")
    
    # Variáveis de controle
    dados = {
        'ativo': True,
        'tempo_decorrido': 0,
        'tempo_total': duracao
    }
    
    def atualizar_progresso():
        """Atualiza a barra de progresso em thread separada"""
        inicio = time.time()
        
        while dados['ativo'] and dados['tempo_decorrido'] < dados['tempo_total']:
            tempo_decorrido = int(time.time() - inicio)
            dados['tempo_decorrido'] = tempo_decorrido
            
            # Calcula progresso
            progresso_pct = int((tempo_decorrido / dados['tempo_total']) * 100)
            progresso_pct = min(progresso_pct, 100)
            
            try:
                progress['value'] = progresso_pct
                janela.update_idletasks()
            except tk.TclError:
                break
            
            time.sleep(0.5)
        
        # Completa a barra
        if dados['ativo']:
            try:
                progress['value'] = 100
                janela.update_idletasks()
                time.sleep(1)
                janela.destroy()
            except tk.TclError:
                pass
    
    # Inicia thread de carregamento
    thread = threading.Thread(target=atualizar_progresso, daemon=True)
    thread.start()
    
    # Adiciona método para fechar manualmente
    def fechar():
        dados['ativo'] = False
        try:
            janela.destroy()
        except tk.TclError:
            pass
    
    janela.fechar = fechar
    
    return janela


if __name__ == "__main__":
    # Cria janela raiz (invisível)
    root = tk.Tk()
    root.withdraw()
    
    # Abre a tela de carregamento
    tela = tela_carregamento(
        titulo="Carregando",
        mensagem="Por favor, aguarde...",
        duracao=60
    )
    
    root.mainloop()
