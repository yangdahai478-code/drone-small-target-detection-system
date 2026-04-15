"""
登录窗口，用户认证与注册。
@作者：Jay
@定制联系vx：Jay8059
@开发日期：2026年
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QStackedWidget, QSizePolicy,
    QGraphicsDropShadowEffect
)
from PyQt6.QtCore import Qt, pyqtSignal, QPropertyAnimation, QEasingCurve, QRect
from PyQt6.QtGui import QColor, QFont, QIcon

from utils.styles import LOGIN_STYLE
from utils import storage


class LoginWindow(QWidget):
    login_success = pyqtSignal(dict)   # 传递用户信息

    def __init__(self):
        super().__init__()
        self.setWindowTitle("无人机航拍小目标检测系统 - 登录")
        self.setMinimumSize(460, 580)
        self.resize(460, 580)
        self.setObjectName("login_bg")
        self.setStyleSheet(LOGIN_STYLE)
        self._build_ui()

    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        # 背景层（铺满窗口，无左右留白）
        bg = QWidget(self)
        bg.setObjectName("login_bg")
        bg_layout = QVBoxLayout(bg)
        bg_layout.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(bg)

        # 卡片铺满，无左右留白
        center_layout = QHBoxLayout()
        center_layout.setContentsMargins(0, 0, 0, 0)

        card = QWidget()
        card.setObjectName("login_card")
        card.setMinimumWidth(400)
        card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(40)
        shadow.setOffset(0, 8)
        shadow.setColor(QColor(59, 130, 246, 70))
        card.setGraphicsEffect(shadow)

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(36, 32, 36, 36)
        card_layout.setSpacing(0)

        # ── 标题区 ──
        icon_label = QLabel("🛸")
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_label.setStyleSheet("font-size: 48px; padding: 0; margin-bottom: 6px;")
        card_layout.addWidget(icon_label)

        title = QLabel("无人机小目标检测系统")
        title.setObjectName("login_app_title")
        card_layout.addWidget(title)

        sub = QLabel("Drone Small Object Detection System")
        sub.setObjectName("login_app_sub")
        card_layout.addWidget(sub)

        card_layout.addSpacing(16)

        # ── 登录/注册 按钮并排居中 ──
        btn_row = QHBoxLayout()
        btn_row.setSpacing(16)
        btn_row.addStretch(1)
        self.login_tab_btn = QPushButton("登  录")
        self.login_tab_btn.setObjectName("login_tab_btn")
        self.login_tab_btn.setCheckable(True)
        self.login_tab_btn.setChecked(True)
        self.login_tab_btn.clicked.connect(lambda: self._switch_to(0))
        self.register_tab_btn = QPushButton("注  册")
        self.register_tab_btn.setObjectName("login_tab_btn")
        self.register_tab_btn.setCheckable(True)
        self.register_tab_btn.clicked.connect(lambda: self._switch_to(1))
        btn_row.addWidget(self.login_tab_btn)
        btn_row.addWidget(self.register_tab_btn)
        btn_row.addStretch(1)
        card_layout.addLayout(btn_row)

        card_layout.addSpacing(12)

        # ── 表单内容堆叠 ──
        self.form_stack = QStackedWidget()
        login_widget = self._build_login_tab()
        register_widget = self._build_register_tab()
        self.form_stack.addWidget(login_widget)
        self.form_stack.addWidget(register_widget)
        card_layout.addWidget(self.form_stack)

        center_layout.addWidget(card, 1)
        bg_layout.addLayout(center_layout, 1)

    def _switch_to(self, index: int):
        self.form_stack.setCurrentIndex(index)
        self.login_tab_btn.setChecked(index == 0)
        self.register_tab_btn.setChecked(index == 1)

    # ─────────────────────────────────────
    def _build_login_tab(self):
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        layout.addStretch(1)
        self.login_username = QLineEdit()
        self.login_username.setObjectName("login_input")
        self.login_username.setPlaceholderText("请输入用户名")
        self.login_username.setMinimumHeight(44)
        layout.addWidget(self.login_username)
        layout.addSpacing(12)

        self.login_password = QLineEdit()
        self.login_password.setObjectName("login_input")
        self.login_password.setEchoMode(QLineEdit.EchoMode.Password)
        self.login_password.setPlaceholderText("请输入密码（默认 admin123）")
        self.login_password.setMinimumHeight(44)
        layout.addWidget(self.login_password)
        layout.addStretch(1)

        self.login_msg = QLabel("")
        self.login_msg.setObjectName("login_error_msg")
        self.login_msg.setMinimumHeight(22)
        layout.addWidget(self.login_msg)

        self.login_btn = QPushButton("登  录")
        self.login_btn.setObjectName("login_submit_btn")
        self.login_btn.setMinimumHeight(48)
        self.login_btn.clicked.connect(self._do_login)
        self.login_password.returnPressed.connect(self._do_login)
        layout.addWidget(self.login_btn)

        layout.addSpacing(8)
        hint = QLabel("默认账号：admin    密码：admin123")
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hint.setStyleSheet("font-family:'SimSun','宋体',serif;font-size:11px;color:rgba(148,163,184,0.8);")
        layout.addWidget(hint)

        return w

    def _build_register_tab(self):
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        layout.addStretch(1)
        self.reg_username = QLineEdit()
        self.reg_username.setObjectName("login_input")
        self.reg_username.setPlaceholderText("请设置用户名（4~16位）")
        self.reg_username.setMinimumHeight(44)
        layout.addWidget(self.reg_username)
        layout.addSpacing(12)

        self.reg_password = QLineEdit()
        self.reg_password.setObjectName("login_input")
        self.reg_password.setEchoMode(QLineEdit.EchoMode.Password)
        self.reg_password.setPlaceholderText("请设置密码（不少于6位）")
        self.reg_password.setMinimumHeight(44)
        layout.addWidget(self.reg_password)
        layout.addSpacing(12)

        self.reg_password2 = QLineEdit()
        self.reg_password2.setObjectName("login_input")
        self.reg_password2.setEchoMode(QLineEdit.EchoMode.Password)
        self.reg_password2.setPlaceholderText("请再次输入密码")
        self.reg_password2.setMinimumHeight(44)
        layout.addWidget(self.reg_password2)
        layout.addStretch(1)

        self.reg_msg = QLabel("")
        self.reg_msg.setObjectName("login_error_msg")
        self.reg_msg.setMinimumHeight(22)
        layout.addWidget(self.reg_msg)

        self.reg_btn = QPushButton("注  册")
        self.reg_btn.setObjectName("login_submit_btn")
        self.reg_btn.setMinimumHeight(48)
        self.reg_btn.clicked.connect(self._do_register)
        layout.addWidget(self.reg_btn)

        return w

    # ─────────────────────────────────────
    def _do_login(self):
        username = self.login_username.text().strip()
        password = self.login_password.text()
        if not username:
            self._show_login_msg("请输入用户名", error=True)
            return
        if not password:
            self._show_login_msg("请输入密码", error=True)
            return
        user = storage.verify_user(username, password)
        if user:
            self._show_login_msg("登录成功，正在进入系统…", error=False)
            cfg = storage.load_config()
            cfg["last_user"] = username
            storage.save_config(cfg)
            # 延迟跳转
            from PyQt6.QtCore import QTimer
            QTimer.singleShot(600, lambda: self.login_success.emit(user))
        else:
            self._show_login_msg("用户名或密码错误", error=True)

    def _do_register(self):
        username = self.reg_username.text().strip()
        password = self.reg_password.text()
        password2 = self.reg_password2.text()
        if not username:
            self._show_reg_msg("用户名不能为空", error=True)
            return
        if len(username) < 3 or len(username) > 20:
            self._show_reg_msg("用户名长度需在3~20位之间", error=True)
            return
        if not password:
            self._show_reg_msg("密码不能为空", error=True)
            return
        if password != password2:
            self._show_reg_msg("两次密码不一致", error=True)
            return
        ok, msg = storage.register_user(username, password)
        if ok:
            self._show_reg_msg(msg, error=False)
            from PyQt6.QtCore import QTimer
            QTimer.singleShot(1000, lambda: self._switch_to(0))
        else:
            self._show_reg_msg(msg, error=True)

    def _show_login_msg(self, msg: str, error: bool = True):
        self.login_msg.setText(msg)
        color = "#FCA5A5" if error else "#67E8F9"
        self.login_msg.setStyleSheet(
            f"font-family:'SimSun','宋体',serif;font-size:12px;color:{color};"
            "qproperty-alignment:AlignCenter;"
        )

    def _show_reg_msg(self, msg: str, error: bool = True):
        self.reg_msg.setText(msg)
        color = "#FCA5A5" if error else "#67E8F9"
        self.reg_msg.setStyleSheet(
            f"font-family:'SimSun','宋体',serif;font-size:12px;color:{color};"
            "qproperty-alignment:AlignCenter;"
        )
