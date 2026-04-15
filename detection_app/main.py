"""
无人机航拍小目标检测系统启动入口，基于 PyQt6 + YOLO11，展示启动画面后进入登录/主界面。
@作者：Jay
@定制联系vx：Jay8059
@开发日期：2026年
"""

import sys
import os
from pathlib import Path

# conda 的 PATH 在导入 PyQt6 之后会恢复，避免影响 torch/ultralytics 等依赖 Library\bin 的库
_ORIGINAL_PATH = os.environ.get("PATH", "")


def _resolve_pyqt6_qt_bin() -> Path | None:
    site_roots: list[Path] = []
    try:
        import site

        for p in site.getsitepackages():
            p = Path(p)
            if p.name == "site-packages":
                site_roots.append(p)
            else:
                nested = p / "Lib" / "site-packages"
                if nested.is_dir():
                    site_roots.append(nested)
        usp = site.getusersitepackages()
        if usp:
            site_roots.append(Path(usp))
    except Exception:
        pass
    site_roots.append(Path(sys.prefix) / "Lib" / "site-packages")
    base = getattr(sys, "base_prefix", sys.prefix)
    site_roots.append(Path(base) / "Lib" / "site-packages")

    seen: set[Path] = set()
    for root in site_roots:
        if root in seen:
            continue
        seen.add(root)
        candidate = root / "PyQt6" / "Qt6" / "bin"
        if candidate.is_dir():
            return candidate
    return None


def _norm_path_key(p: str) -> str:
    return os.path.normcase(os.path.normpath(p))


def _prepend_pyqt6_qt_dll_paths(bin_dir: Path) -> None:
    """优先使用 pip 自带 Qt6；并从 PATH 中暂时拿掉 conda 的 Library\\bin，避免先载入错误版本的 Qt6*.dll。"""
    s = str(bin_dir)
    if hasattr(os, "add_dll_directory"):
        os.add_dll_directory(s)

    block = {
        _norm_path_key(str(Path(sys.prefix) / "Library" / "bin")),
        _norm_path_key(str(Path(getattr(sys, "base_prefix", sys.prefix)) / "Library" / "bin")),
    }
    block.discard(_norm_path_key(""))  # if prefix odd

    parts = [
        p
        for p in _ORIGINAL_PATH.split(os.pathsep)
        if p and _norm_path_key(p) not in block
    ]
    os.environ["PATH"] = s + os.pathsep + os.pathsep.join(parts)

    plugins = bin_dir.parent / "plugins"
    if plugins.is_dir():
        os.environ["QT_PLUGIN_PATH"] = str(plugins)


_qt_bin = _resolve_pyqt6_qt_bin()
if _qt_bin is not None:
    _prepend_pyqt6_qt_dll_paths(_qt_bin)

# 确保在 detection_app 目录下运行
APP_DIR = os.path.dirname(os.path.abspath(__file__))
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)

from PyQt6.QtWidgets import QApplication, QSplashScreen, QLabel
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QColor, QPixmap, QPainter, QLinearGradient

if sys.platform == "win32" and _qt_bin is not None:
    # 恢复完整 PATH（含 Library\bin），PyQt6 的 Qt6 DLL 已在进程中；PyQt6 bin 仍放最前以降低后续冲突
    os.environ["PATH"] = str(_qt_bin) + os.pathsep + _ORIGINAL_PATH

from login_window import LoginWindow
from main_window import MainWindow


def create_splash() -> QSplashScreen:
    """创建启动画面"""
    pixmap = QPixmap(520, 300)
    pixmap.fill(Qt.GlobalColor.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    grad = QLinearGradient(0, 0, 520, 300)
    grad.setColorAt(0, QColor("#34D399"))
    grad.setColorAt(0.5, QColor("#10B981"))
    grad.setColorAt(1, QColor("#059669"))
    painter.setBrush(grad)
    painter.setPen(Qt.PenStyle.NoPen)
    painter.drawRoundedRect(0, 0, 520, 300, 16, 16)

    painter.setPen(QColor(255, 255, 255))
    font = QFont("KaiTi", 28, QFont.Weight.Bold)
    painter.setFont(font)
    painter.drawText(pixmap.rect().adjusted(0, 60, 0, -100),
                     Qt.AlignmentFlag.AlignCenter, "🛸  无人机小目标检测系统")

    font2 = QFont("SimSun", 13)
    painter.setFont(font2)
    painter.setPen(QColor(255, 255, 255, 180))
    painter.drawText(pixmap.rect().adjusted(0, 130, 0, -60),
                     Qt.AlignmentFlag.AlignCenter,
                     "Drone Small Object Detection System")

    painter.setPen(QColor(255, 255, 255, 120))
    font3 = QFont("SimSun", 11)
    painter.setFont(font3)
    painter.drawText(pixmap.rect().adjusted(0, 200, 0, -20),
                     Qt.AlignmentFlag.AlignCenter,
                     "YOLOv11  |  VisDrone 2019")

    painter.end()

    splash = QSplashScreen(pixmap)
    splash.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.SplashScreen)
    return splash


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("无人机航拍小目标检测系统")
    app.setOrganizationName("DroneDetection")

    # 全局字体
    default_font = QFont("SimSun", 12)
    app.setFont(default_font)

    # 启动画面
    splash = create_splash()
    splash.show()
    app.processEvents()

    login_win_holder = {}

    def show_login():
        splash.close()
        login_win = LoginWindow()

        def on_login_success(user_info: dict):
            login_win.close()
            main_win = MainWindow(user_info)
            main_win.show()
            login_win_holder["main_win"] = main_win

        login_win.login_success.connect(on_login_success)
        login_win.show()
        login_win_holder["login_win"] = login_win

    QTimer.singleShot(1800, show_login)
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
