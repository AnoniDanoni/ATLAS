import os
import sys

# Executar comando
os.system(f'"{sys.executable}" -m PyInstaller --onefile --icon=atlas_icon.ico --noconsole ATLAS.py')

# Executar comando do sistema
os.system("dir")  # Windows
# os.system("ls")  # Linux/Mac