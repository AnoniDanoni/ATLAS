import os

# Executar comando
os.system("pyinstaller --onefile --icon=atlas_icon.ico --noconsole ATLAS.py")

# Executar comando do sistema
os.system("dir")  # Windows
# os.system("ls")  # Linux/Mac