"""
全局样式定义，深空蓝渐变主题（主窗口、登录、滚动条等）。
@作者：Jay
@定制联系vx：Jay8059
@开发日期：2026年
"""

MAIN_STYLE = """
/* ========== 全局 ========== */
* {
    outline: none;
}

QMainWindow {
    background-color: #0f172a;
}

QWidget {
    font-family: "SimSun", "宋体", serif;
}

/* ========== 滚动条 ========== */
QScrollBar:vertical {
    background: rgba(30, 41, 59, 0.8);
    width: 8px;
    border-radius: 4px;
    margin: 0;
}
QScrollBar::handle:vertical {
    background: rgba(59, 130, 246, 0.6);
    border-radius: 4px;
    min-height: 24px;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QScrollBar:horizontal {
    background: rgba(30, 41, 59, 0.8);
    height: 8px;
    border-radius: 4px;
    margin: 0;
}
QScrollBar::handle:horizontal {
    background: rgba(59, 130, 246, 0.6);
    border-radius: 4px;
    min-width: 24px;
}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0; }

/* ========== 侧边栏 ========== */
QWidget#sidebar {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #1e3a5f, stop:0.5 #1e293b, stop:1 #0f172a);
    min-width: 200px;
    max-width: 200px;
}

/* ========== 侧边栏标题 ========== */
QLabel#sidebar_logo_title {
    font-family: "KaiTi", "楷体", serif;
    font-size: 23px;
    font-weight: bold;
    color: #E0F2FE;
    qproperty-alignment: AlignCenter;
    padding: 6px 4px 2px 4px;
    letter-spacing: 1px;
}
QLabel#sidebar_logo_sub {
    font-family: "KaiTi", "楷体", serif;
    font-size: 11px;
    color: rgba(148, 163, 184, 0.8);
    qproperty-alignment: AlignCenter;
    padding: 0 4px 8px 4px;
}

QFrame#sidebar_divider {
    background: rgba(59, 130, 246, 0.3);
    max-height: 1px;
    margin: 4px 16px;
}

/* ========== 导航按钮 ========== */
QPushButton#nav_btn {
    font-family: "KaiTi", "楷体", serif;
    font-size: 16px;
    font-weight: bold;
    color: rgba(226, 232, 240, 0.85);
    text-align: center;
    background: transparent;
    border: none;
    border-radius: 10px;
    padding: 11px 8px;
    margin: 3px 14px;
}
QPushButton#nav_btn:hover {
    background: rgba(59, 130, 246, 0.2);
    color: #93C5FD;
}
QPushButton#nav_btn[active="true"] {
    background: rgba(59, 130, 246, 0.25);
    color: #60A5FA;
    border-left: 4px solid #3B82F6;
    padding-left: 12px;
}

/* ========== 侧边栏用户区 ========== */
QWidget#sidebar_user_area {
    background: rgba(15, 23, 42, 0.6);
    border-radius: 10px;
    margin: 8px 12px;
    padding: 6px;
}
QLabel#sidebar_username {
    font-family: "KaiTi", "楷体", serif;
    font-size: 13px;
    font-weight: bold;
    color: #E0F2FE;
    qproperty-alignment: AlignCenter;
}
QLabel#sidebar_user_role {
    font-family: "SimSun", "宋体", serif;
    font-size: 11px;
    color: rgba(148, 163, 184, 0.8);
    qproperty-alignment: AlignCenter;
}
QPushButton#logout_btn {
    font-family: "KaiTi", "楷体", serif;
    font-size: 14px;
    color: #FCA5A5;
    background: rgba(239, 68, 68, 0.25);
    border: 1px solid rgba(248, 113, 113, 0.4);
    border-radius: 8px;
    padding: 4px 12px;
    margin-top: 4px;
}
QPushButton#logout_btn:hover {
    background: rgba(239, 68, 68, 0.4);
    color: #FFFFFF;
}

/* ========== 内容区背景 ========== */
QWidget#content_area {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 #0f172a, stop:0.5 #0c1222, stop:1 #0a1628);
}

/* ========== 页面顶部标题栏 ========== */
QWidget#page_header {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #1e293b, stop:1 #0f172a);
    border-bottom: 2px solid rgba(59, 130, 246, 0.35);
    min-height: 72px;
    max-height: 72px;
}
QLabel#page_title {
    font-family: "KaiTi", "楷体", serif;
    font-size: 22px;
    font-weight: bold;
    color: #E0F2FE;
    qproperty-alignment: AlignCenter;
    padding: 8px 20px;
}
QLabel#page_subtitle {
    font-family: "SimSun", "宋体", serif;
    font-size: 12px;
    color: rgba(148, 163, 184, 0.9);
    qproperty-alignment: AlignCenter;
}

/* ========== 卡片容器 ========== */
QWidget#card {
    background: rgba(30, 41, 59, 0.9);
    border-radius: 14px;
    border: 1px solid rgba(59, 130, 246, 0.35);
}
QLabel#card_title {
    font-family: "KaiTi", "楷体", serif;
    font-size: 15px;
    font-weight: bold;
    color: #93C5FD;
    qproperty-alignment: AlignCenter;
    padding: 8px 12px 4px 12px;
    border-bottom: 1px solid rgba(59, 130, 246, 0.3);
}

/* ========== 主要按钮 ========== */
QPushButton#primary_btn {
    font-family: "KaiTi", "楷体", serif;
    font-size: 16px;
    font-weight: bold;
    color: #FFFFFF;
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #3B82F6, stop:0.5 #2563EB, stop:1 #1D4ED8);
    border: none;
    border-radius: 10px;
    padding: 10px 24px;
    min-width: 100px;
}
QPushButton#primary_btn:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #60A5FA, stop:0.5 #3B82F6, stop:1 #2563EB);
}
QPushButton#primary_btn:pressed {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #2563EB, stop:1 #1E40AF);
}
QPushButton#primary_btn:disabled {
    background: #475569;
    color: rgba(255,255,255,0.5);
}

/* ========== 次要按钮 ========== */
QPushButton#secondary_btn {
    font-family: "KaiTi", "楷体", serif;
    font-size: 16px;
    font-weight: bold;
    color: #60A5FA;
    background: transparent;
    border: 2px solid rgba(59, 130, 246, 0.6);
    border-radius: 10px;
    padding: 8px 20px;
    min-width: 90px;
}
QPushButton#secondary_btn:hover {
    background: rgba(59, 130, 246, 0.15);
    border-color: #3B82F6;
    color: #93C5FD;
}
QPushButton#secondary_btn:pressed {
    background: rgba(59, 130, 246, 0.25);
}
QPushButton#secondary_btn:disabled {
    color: #64748B;
    border-color: #475569;
}

/* ========== 危险/停止按钮 ========== */
QPushButton#danger_btn {
    font-family: "KaiTi", "楷体", serif;
    font-size: 16px;
    font-weight: bold;
    color: #FFFFFF;
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #EF4444, stop:1 #DC2626);
    border: none;
    border-radius: 10px;
    padding: 10px 24px;
    min-width: 100px;
}
QPushButton#danger_btn:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #F87171, stop:1 #EF4444);
}

/* ========== 成功/开始按钮 ========== */
QPushButton#success_btn {
    font-family: "KaiTi", "楷体", serif;
    font-size: 16px;
    font-weight: bold;
    color: #FFFFFF;
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #3B82F6, stop:0.5 #2563EB, stop:1 #1D4ED8);
    border: none;
    border-radius: 10px;
    padding: 10px 24px;
    min-width: 100px;
}
QPushButton#success_btn:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #60A5FA, stop:0.5 #3B82F6, stop:1 #2563EB);
}
QPushButton#success_btn:disabled {
    background: #475569;
}

/* ========== 表格 ========== */
QTableWidget {
    background: rgba(30, 41, 59, 0.9);
    border: 1px solid rgba(59, 130, 246, 0.35);
    border-radius: 8px;
    gridline-color: rgba(59, 130, 246, 0.2);
    font-family: "SimSun", "宋体", serif;
    font-size: 13px;
    color: #E2E8F0;
    selection-background-color: rgba(59, 130, 246, 0.35);
    selection-color: #E0F2FE;
}
QTableWidget::item {
    padding: 6px 10px;
    border: none;
    qproperty-alignment: AlignCenter;
}
QTableWidget::item:selected {
    background: rgba(59, 130, 246, 0.35);
}
QHeaderView::section {
    font-family: "KaiTi", "楷体", serif;
    font-size: 13px;
    font-weight: bold;
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #1e3a5f, stop:1 #1e293b);
    color: #93C5FD;
    padding: 7px 10px;
    border: none;
    border-right: 1px solid rgba(59, 130, 246, 0.25);
    border-bottom: 2px solid rgba(59, 130, 246, 0.35);
    qproperty-alignment: AlignCenter;
}
QHeaderView::section:last { border-right: none; }

/* ========== 输入框 ========== */
QLineEdit {
    font-family: "SimSun", "宋体", serif;
    font-size: 14px;
    color: #E2E8F0;
    background: rgba(15, 23, 42, 0.8);
    border: 2px solid rgba(59, 130, 246, 0.4);
    border-radius: 10px;
    padding: 8px 14px;
}
QLineEdit:focus {
    border-color: #3B82F6;
    background: rgba(30, 41, 59, 0.95);
}
QLineEdit:hover {
    border-color: rgba(59, 130, 246, 0.6);
}

/* ========== 标签文字 ========== */
QLabel#label_field {
    font-family: "SimSun", "宋体", serif;
    font-size: 13px;
    color: #93C5FD;
    qproperty-alignment: AlignCenter;
}
QLabel#value_field {
    font-family: "SimSun", "宋体", serif;
    font-size: 14px;
    font-weight: bold;
    color: #E2E8F0;
    qproperty-alignment: AlignCenter;
}
QLabel#stat_number {
    font-family: "KaiTi", "楷体", serif;
    font-size: 28px;
    font-weight: bold;
    color: #60A5FA;
    qproperty-alignment: AlignCenter;
}
QLabel#stat_label {
    font-family: "SimSun", "宋体", serif;
    font-size: 12px;
    color: rgba(148, 163, 184, 0.9);
    qproperty-alignment: AlignCenter;
}

/* ========== ComboBox ========== */
QComboBox {
    font-family: "SimSun", "宋体", serif;
    font-size: 13px;
    color: #E2E8F0;
    background: rgba(30, 41, 59, 0.9);
    border: 2px solid rgba(59, 130, 246, 0.4);
    border-radius: 8px;
    padding: 6px 10px;
    min-width: 120px;
}
QComboBox:focus { border-color: #3B82F6; }
QComboBox::drop-down {
    border: none;
    width: 24px;
}
QComboBox QAbstractItemView {
    background: #1e293b;
    border: 1px solid rgba(59, 130, 246, 0.35);
    border-radius: 8px;
    selection-background-color: rgba(59, 130, 246, 0.35);
    color: #E2E8F0;
    font-family: "SimSun", "宋体", serif;
}

/* ========== 进度条 ========== */
QProgressBar {
    background: rgba(30, 41, 59, 0.8);
    border-radius: 6px;
    height: 12px;
    border: none;
    text-align: center;
    font-size: 11px;
    color: #93C5FD;
}
QProgressBar::chunk {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #3B82F6, stop:0.5 #2563EB, stop:1 #1D4ED8);
    border-radius: 6px;
}

/* ========== 标签页 ========== */
QTabWidget::pane {
    background: rgba(30, 41, 59, 0.9);
    border: 1px solid rgba(59, 130, 246, 0.35);
    border-radius: 0 10px 10px 10px;
}
QTabBar::tab {
    font-family: "KaiTi", "楷体", serif;
    font-size: 15px;
    font-weight: bold;
    color: rgba(148, 163, 184, 0.9);
    background: rgba(15, 23, 42, 0.8);
    border: 1px solid rgba(59, 130, 246, 0.3);
    border-bottom: none;
    border-radius: 8px 8px 0 0;
    padding: 7px 18px;
    margin-right: 3px;
}
QTabBar::tab:selected {
    background: rgba(30, 41, 59, 0.95);
    color: #60A5FA;
    border-bottom: 2px solid #3B82F6;
}
QTabBar::tab:hover { background: rgba(59, 130, 246, 0.15); color: #93C5FD; }

/* ========== 文本框 ========== */
QTextEdit, QPlainTextEdit {
    font-family: "SimSun", "宋体", serif;
    font-size: 13px;
    color: #E2E8F0;
    background: rgba(15, 23, 42, 0.8);
    border: 1px solid rgba(59, 130, 246, 0.35);
    border-radius: 8px;
    padding: 8px;
}

/* ========== 复选框 ========== */
QCheckBox {
    font-family: "SimSun", "宋体", serif;
    font-size: 13px;
    color: #E2E8F0;
    spacing: 6px;
}
QCheckBox::indicator {
    width: 16px; height: 16px;
    border-radius: 4px;
    border: 2px solid rgba(59, 130, 246, 0.6);
    background: rgba(15, 23, 42, 0.8);
}
QCheckBox::indicator:checked {
    background: #3B82F6;
    border-color: #3B82F6;
}

/* ========== Slider ========== */
QSlider::groove:horizontal {
    background: rgba(30, 41, 59, 0.8);
    height: 6px;
    border-radius: 3px;
}
QSlider::handle:horizontal {
    background: #3B82F6;
    width: 16px; height: 16px;
    margin: -5px 0;
    border-radius: 8px;
}
QSlider::sub-page:horizontal {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #3B82F6, stop:0.5 #2563EB, stop:1 #1D4ED8);
    border-radius: 3px;
}
"""

# 深空蓝渐变风格 - 登录界面
LOGIN_STYLE = """
QWidget#login_bg {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 #0f172a,
        stop:0.35 #0c1222,
        stop:0.65 #0a1628,
        stop:1 #020617);
}

QWidget#login_card {
    background: rgba(30, 41, 59, 0.92);
    border-radius: 20px;
    border: 1px solid rgba(59, 130, 246, 0.35);
}

QLabel#login_app_title {
    font-family: "KaiTi", "楷体", serif;
    font-size: 30px;
    font-weight: bold;
    color: #E0F2FE;
    qproperty-alignment: AlignCenter;
}
QLabel#login_app_sub {
    font-family: "KaiTi", "楷体", serif;
    font-size: 13px;
    color: rgba(148, 163, 184, 0.9);
    qproperty-alignment: AlignCenter;
}

QPushButton#login_tab_btn {
    font-family: "KaiTi", "楷体", serif;
    font-size: 18px;
    font-weight: bold;
    color: rgba(148, 163, 184, 0.9);
    background: transparent;
    border: none;
    border-bottom: 3px solid transparent;
    padding: 8px 32px;
    min-width: 100px;
}
QPushButton#login_tab_btn:hover {
    color: #93C5FD;
}
QPushButton#login_tab_btn:checked {
    color: #60A5FA;
    border-bottom: 3px solid #3B82F6;
}

QLabel#form_label {
    font-family: "SimSun", "宋体", serif;
    font-size: 13px;
    color: #93C5FD;
}

QLineEdit#login_input {
    font-family: "SimSun", "宋体", serif;
    font-size: 14px;
    color: #E2E8F0;
    background: rgba(15, 23, 42, 0.7);
    border: 2px solid rgba(59, 130, 246, 0.4);
    border-radius: 10px;
    padding: 10px 16px;
}
QLineEdit#login_input:focus {
    border-color: #3B82F6;
    background: rgba(30, 41, 59, 0.9);
}
QLineEdit#login_input::placeholder {
    color: rgba(148, 163, 184, 0.6);
}

QPushButton#login_submit_btn {
    font-family: "KaiTi", "楷体", serif;
    font-size: 22px;
    font-weight: bold;
    color: #FFFFFF;
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #3B82F6, stop:0.5 #2563EB, stop:1 #1D4ED8);
    border: none;
    border-radius: 12px;
    padding: 12px 0;
    min-height: 44px;
}
QPushButton#login_submit_btn:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #60A5FA, stop:0.5 #3B82F6, stop:1 #2563EB);
}
QPushButton#login_submit_btn:pressed {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #2563EB, stop:1 #1E40AF);
}

QLabel#login_error_msg {
    font-family: "SimSun", "宋体", serif;
    font-size: 12px;
    color: #FCA5A5;
    qproperty-alignment: AlignCenter;
}
QLabel#login_success_msg {
    font-family: "SimSun", "宋体", serif;
    font-size: 12px;
    color: #67E8F9;
    qproperty-alignment: AlignCenter;
}
"""
