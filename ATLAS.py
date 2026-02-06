# -*- coding: utf-8 -*-
# ATLAS.py - Wrapper para a aplicação refatorada
# 
# Este arquivo funciona como ponto de entrada da aplicação ATLAS.
# A lógica foi refatorada em 3 módulos:
# - core.py: Lógica central (configuração, monitoramento, detecção de Revit)
# - ui.py: Classes de interface (janelas)  
# - main.py: Aplicação principal (MonitorApp)

from main import MonitorApp

if __name__ == "__main__":
    app = MonitorApp()
    app.mainloop()
