@echo off
chcp 65001 >nul
echo 用于 Anaconda 下 pip 版 PyQt6 与 conda 自带 Qt 冲突、出现 DLL 加载失败时。
echo 将在当前已激活的 conda 环境中卸载 pip 的 PyQt6，并改用 conda-forge 的 pyqt6。
echo.
pause
pip uninstall -y PyQt6 PyQt6-Qt6 PyQt6-sip
conda install -y -c conda-forge "pyqt6>=6.4"
echo.
echo 安装完成后请运行: python main.py
pause
