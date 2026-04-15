"""
主窗口，侧边导航与多页面切换（图片/视频/摄像头/历史/模型/指标）。
@作者：Jay
@定制联系vx：Jay8059
@开发日期：2026年
"""

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QLabel, QPushButton, QStackedWidget, QFrame,
    QSizePolicy, QSpacerItem, QGraphicsDropShadowEffect
)
from PyQt6.QtCore import Qt, QPropertyAnimation, QEasingCurve, pyqtSlot
from PyQt6.QtGui import QColor, QFont, QIcon

from utils.styles import MAIN_STYLE

# 导入各页面
from pages.image_page import ImagePage
from pages.video_page import VideoPage
from pages.camera_page import CameraPage
from pages.history_page import HistoryPage
from pages.model_page import ModelPage
from pages.metrics_page import MetricsPage


NAV_ITEMS = [
    ("🖼️", "图片识别", "image"),
    ("🎬", "视频识别", "video"),
    ("📷", "摄像头识别", "camera"),
    ("📋", "检测历史", "history"),
    ("⚙️", "模型管理", "model"),
    ("📊", "指标展示", "metrics"),
]

PAGE_SUBTITLES = {
    "image": "支持JPG/PNG/BMP等格式，上传图片后点击开始检测",
    "video": "支持MP4/AVI/MOV等格式，加载视频后逐帧检测",
    "camera": "实时调用本地摄像头进行目标检测",
    "history": "查看所有历史检测记录，支持筛选与导出（只读）",
    "model": "管理检测模型文件，调整置信度等检测参数",
    "metrics": "展示模型训练过程的各项可视化指标与图表",
}


class MainWindow(QMainWindow):
    def __init__(self, user_info: dict):
        super().__init__()
        self.user_info = user_info
        self.current_page = "image"
        self.nav_buttons = {}

        self.setWindowTitle("无人机航拍小目标检测系统")
        self.setMinimumSize(1200, 750)
        self.resize(1400, 860)
        self.setStyleSheet(MAIN_STYLE)

        self._build_ui()
        self._navigate_to("image")

    def _build_ui(self):
        central = QWidget()
        central.setObjectName("central_widget")
        self.setCentralWidget(central)

        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── 侧边栏 ──
        sidebar = self._build_sidebar()
        root.addWidget(sidebar)

        # ── 内容区 ──
        content_wrapper = QWidget()
        content_wrapper.setObjectName("content_area")
        content_layout = QVBoxLayout(content_wrapper)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        # 顶部标题栏
        self.page_header = self._build_page_header()
        content_layout.addWidget(self.page_header)

        # 页面堆栈
        self.stack = QStackedWidget()
        self.stack.setObjectName("content_area")
        content_layout.addWidget(self.stack)

        # 创建页面
        self.image_page = ImagePage(self.user_info)
        self.video_page = VideoPage(self.user_info)
        self.camera_page = CameraPage(self.user_info)
        self.history_page = HistoryPage(self.user_info)
        self.model_page = ModelPage(self.user_info)
        self.metrics_page = MetricsPage(self.user_info)

        self.pages = {
            "image": self.image_page,
            "video": self.video_page,
            "camera": self.camera_page,
            "history": self.history_page,
            "model": self.model_page,
            "metrics": self.metrics_page,
        }
        for page in self.pages.values():
            self.stack.addWidget(page)

        # 跨页信号连接
        self.image_page.request_history_refresh.connect(self.history_page.refresh_data)
        self.video_page.request_history_refresh.connect(self.history_page.refresh_data)
        self.camera_page.request_history_refresh.connect(self.history_page.refresh_data)
        self.model_page.model_changed.connect(self._on_model_changed)

        root.addWidget(content_wrapper)

    # ─── 侧边栏 ───
    def _build_sidebar(self) -> QWidget:
        sidebar = QWidget()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(200)

        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Logo 区
        logo_area = QWidget()
        logo_area.setStyleSheet("background:transparent;")
        logo_layout = QVBoxLayout(logo_area)
        logo_layout.setContentsMargins(12, 20, 12, 12)
        logo_layout.setSpacing(2)

        icon_lbl = QLabel("🛸")
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_lbl.setStyleSheet("font-size: 36px; background:transparent;")
        logo_layout.addWidget(icon_lbl)

        title_lbl = QLabel("无人机目标检测")
        title_lbl.setObjectName("sidebar_logo_title")
        logo_layout.addWidget(title_lbl)

        sub_lbl = QLabel("Drone Object Detection")
        sub_lbl.setObjectName("sidebar_logo_sub")
        logo_layout.addWidget(sub_lbl)

        layout.addWidget(logo_area)

        # 分割线
        divider = QFrame()
        divider.setObjectName("sidebar_divider")
        divider.setFrameShape(QFrame.Shape.HLine)
        divider.setStyleSheet("background:rgba(59,130,246,0.3);margin:0 16px;max-height:1px;")
        layout.addWidget(divider)

        layout.addSpacing(8)

        # 导航按钮
        nav_section_lbl = QLabel("功   能   导   航")
        nav_section_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        nav_section_lbl.setStyleSheet(
            "font-family:'SimSun','宋体',serif;font-size:10px;"
            "color:rgba(148,163,184,0.7);padding:4px 0;background:transparent;letter-spacing:2px;"
        )
        layout.addWidget(nav_section_lbl)
        layout.addSpacing(4)

        for icon, label, key in NAV_ITEMS:
            btn = QPushButton(f"{icon}  {label}")
            btn.setObjectName("nav_btn")
            btn.setCheckable(False)
            btn.setProperty("active", "false")
            btn.clicked.connect(lambda checked, k=key: self._navigate_to(k))
            layout.addWidget(btn)
            self.nav_buttons[key] = btn

        layout.addStretch()

        # 用户区
        divider2 = QFrame()
        divider2.setFrameShape(QFrame.Shape.HLine)
        divider2.setStyleSheet("background:rgba(59,130,246,0.25);margin:0 16px;max-height:1px;")
        layout.addWidget(divider2)

        user_area = QWidget()
        user_area.setObjectName("sidebar_user_area")
        user_layout = QVBoxLayout(user_area)
        user_layout.setContentsMargins(10, 8, 10, 8)
        user_layout.setSpacing(4)

        avatar_lbl = QLabel("👤")
        avatar_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        avatar_lbl.setStyleSheet("font-size:22px;background:transparent;")
        user_layout.addWidget(avatar_lbl)

        username_lbl = QLabel(self.user_info.get("username", "用户"))
        username_lbl.setObjectName("sidebar_username")
        user_layout.addWidget(username_lbl)

        role_lbl = QLabel(self.user_info.get("role", "普通用户"))
        role_lbl.setObjectName("sidebar_user_role")
        user_layout.addWidget(role_lbl)

        logout_btn = QPushButton("退出登录")
        logout_btn.setObjectName("logout_btn")
        logout_btn.clicked.connect(self._logout)
        user_layout.addWidget(logout_btn)

        layout.addWidget(user_area)
        layout.addSpacing(12)

        return sidebar

    # ─── 顶部标题栏 ───
    def _build_page_header(self) -> QWidget:
        header = QWidget()
        header.setObjectName("page_header")
        header.setFixedHeight(72)

        layout = QVBoxLayout(header)
        layout.setContentsMargins(20, 6, 20, 6)
        layout.setSpacing(2)

        self.page_title_lbl = QLabel("图片识别")
        self.page_title_lbl.setObjectName("page_title")
        layout.addWidget(self.page_title_lbl)

        self.page_sub_lbl = QLabel("支持JPG/PNG/BMP等格式，上传图片后点击开始检测")
        self.page_sub_lbl.setObjectName("page_subtitle")
        layout.addWidget(self.page_sub_lbl)

        return header

    # ─── 导航 ───
    def _navigate_to(self, key: str):
        if key not in self.pages:
            return
        self.current_page = key

        # 更新按钮激活状态
        for k, btn in self.nav_buttons.items():
            active = "true" if k == key else "false"
            btn.setProperty("active", active)
            btn.style().unpolish(btn)
            btn.style().polish(btn)

        # 切换页面
        self.stack.setCurrentWidget(self.pages[key])

        # 更新顶部标题
        icon, label, _ = next(item for item in NAV_ITEMS if item[2] == key)
        self.page_title_lbl.setText(f"{icon}  {label}")
        self.page_sub_lbl.setText(PAGE_SUBTITLES.get(key, ""))

        # 特殊页面刷新
        if key == "history":
            self.history_page.refresh_data()
        elif key == "metrics":
            self.metrics_page._load_data()
        elif key == "model":
            self.model_page._load_current_config()

    @pyqtSlot(str)
    def _on_model_changed(self, new_path: str):
        pass  # 可扩展：通知各检测页刷新模型

    def _logout(self):
        from PyQt6.QtWidgets import QMessageBox
        reply = QMessageBox.question(
            self, "退出登录",
            "确定要退出当前账号吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            # 停止摄像头（如果在运行）
            if self.camera_page.worker and self.camera_page.worker.isRunning():
                self.camera_page.worker.stop()
                self.camera_page.worker.wait()
            self.close()
            # 重新打开登录窗口
            from login_window import LoginWindow
            self._login_win = LoginWindow()
            self._login_win.login_success.connect(self._on_relogin)
            self._login_win.show()

    def _on_relogin(self, user_info: dict):
        self._login_win.close()
        new_win = MainWindow(user_info)
        new_win.show()
        self._login_win._main_win = new_win

    def closeEvent(self, event):
        if self.camera_page.worker and self.camera_page.worker.isRunning():
            self.camera_page.worker.stop()
            self.camera_page.worker.wait()
        if self.video_page.worker and self.video_page.worker.isRunning():
            self.video_page.worker.stop()
            self.video_page.worker.wait()
        event.accept()
