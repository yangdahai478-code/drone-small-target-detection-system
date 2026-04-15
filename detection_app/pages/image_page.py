"""
图片检测页面，支持单图/批量上传、YOLO 检测、结果表格与可视化。
@作者：Jay
@定制联系vx：Jay8059
@开发日期：2026年
"""

import os
import csv
import numpy as np
from datetime import datetime
from pathlib import Path

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFileDialog, QScrollArea, QTableWidget, QTableWidgetItem,
    QSplitter, QFrame, QSizePolicy, QProgressBar, QGridLayout,
    QSpacerItem, QMessageBox, QTabWidget, QHeaderView
)
from PyQt6.QtCore import Qt, pyqtSignal, QThread
from PyQt6.QtGui import QPixmap, QImage, QColor, QFont

import matplotlib
matplotlib.use("QtAgg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from utils.detector import ImageDetectWorker, save_results_csv
from utils import storage


def ndarray_to_pixmap(arr) -> QPixmap:
    import cv2
    rgb = cv2.cvtColor(arr, cv2.COLOR_BGR2RGB)
    h, w, ch = rgb.shape
    img = QImage(rgb.data, w, h, ch * w, QImage.Format.Format_RGB888)
    return QPixmap.fromImage(img)


class ImagePage(QWidget):
    request_history_refresh = pyqtSignal()

    def __init__(self, user_info: dict):
        super().__init__()
        self.user_info = user_info
        self.current_image_path = ""
        self.detected_data = None
        self.annotated_arr = None
        self.worker = None
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 12, 16, 12)
        root.setSpacing(10)

        # ── 顶部工具栏 ──
        toolbar = self._build_toolbar()
        root.addWidget(toolbar)

        # ── 主体分割视图 ──
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setHandleWidth(6)
        splitter.setStyleSheet("QSplitter::handle { background: rgba(59,130,246,0.5); border-radius: 3px; }")

        # 左：图片预览
        left_panel = self._build_left_panel()
        splitter.addWidget(left_panel)

        # 右：识别结果
        right_panel = self._build_right_panel()
        splitter.addWidget(right_panel)

        splitter.setSizes([520, 580])
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 1)
        root.addWidget(splitter)

        # ── 底部状态区（含普通状态条 + 检测完成横幅）──
        self.status_stack = QWidget()
        status_layout = QVBoxLayout(self.status_stack)
        status_layout.setContentsMargins(0, 0, 0, 0)
        status_layout.setSpacing(0)

        self.status_bar = QLabel("请点击【打开图片】选择要检测的图片")
        self.status_bar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_bar.setStyleSheet(
            "font-family:'SimSun','宋体',serif;font-size:12px;color:#93C5FD;"
            "background:rgba(30,41,59,0.9);border-radius:6px;padding:5px;border:1px solid rgba(59,130,246,0.3);"
        )
        status_layout.addWidget(self.status_bar)

        # 检测完成醒目横幅（默认隐藏）
        self.success_banner = QFrame()
        self.success_banner.setObjectName("success_banner")
        self.success_banner.setStyleSheet("""
            QFrame#success_banner {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(34, 197, 94, 0.25),
                    stop:0.5 rgba(59, 130, 246, 0.3),
                    stop:1 rgba(34, 197, 94, 0.25));
                border: 2px solid rgba(34, 197, 94, 0.6);
                border-radius: 12px;
                margin-top: 8px;
            }
        """)
        self.success_banner.setVisible(False)
        banner_layout = QVBoxLayout(self.success_banner)
        banner_layout.setContentsMargins(20, 14, 20, 14)
        banner_layout.setSpacing(4)

        self.success_icon = QLabel("✓")
        self.success_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.success_icon.setStyleSheet(
            "font-size: 28px; font-weight: bold; color: #22C55E; "
            "background: transparent;"
        )
        banner_layout.addWidget(self.success_icon)

        self.success_title = QLabel("检测完成")
        self.success_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.success_title.setStyleSheet(
            "font-family:'KaiTi','楷体',serif; font-size: 20px; font-weight: bold; "
            "color: #67E8F9; background: transparent;"
        )
        banner_layout.addWidget(self.success_title)

        self.success_detail = QLabel("")
        self.success_detail.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.success_detail.setStyleSheet(
            "font-family:'SimSun','宋体',serif; font-size: 14px; "
            "color: #93C5FD; background: transparent;"
        )
        banner_layout.addWidget(self.success_detail)

        status_layout.addWidget(self.success_banner)
        root.addWidget(self.status_stack)

    # ─────────────────────────────────────
    def _build_toolbar(self):
        bar = QWidget()
        bar.setObjectName("card")
        bar.setMaximumHeight(64)
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(16, 8, 16, 8)
        layout.setSpacing(10)

        self.open_btn = QPushButton("📂  打开图片")
        self.open_btn.setObjectName("primary_btn")
        self.open_btn.clicked.connect(self._open_image)

        self.detect_btn = QPushButton("🔍  开始检测")
        self.detect_btn.setObjectName("success_btn")
        self.detect_btn.setEnabled(False)
        self.detect_btn.clicked.connect(self._start_detect)

        self.export_img_btn = QPushButton("🖼  导出图片")
        self.export_img_btn.setObjectName("secondary_btn")
        self.export_img_btn.setEnabled(False)
        self.export_img_btn.clicked.connect(self._export_image)

        self.export_csv_btn = QPushButton("📊  导出CSV")
        self.export_csv_btn.setObjectName("secondary_btn")
        self.export_csv_btn.setEnabled(False)
        self.export_csv_btn.clicked.connect(self._export_csv)

        self.clear_btn = QPushButton("🗑  清除")
        self.clear_btn.setObjectName("secondary_btn")
        self.clear_btn.clicked.connect(self._clear)

        for b in [self.open_btn, self.detect_btn, self.export_img_btn,
                  self.export_csv_btn, self.clear_btn]:
            layout.addWidget(b)

        layout.addStretch()

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)
        self.progress_bar.setFixedWidth(140)
        self.progress_bar.setFixedHeight(14)
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        return bar

    def _build_left_panel(self):
        panel = QWidget()
        panel.setObjectName("card")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 8, 10, 10)
        layout.setSpacing(6)

        title = QLabel("图  片  预  览")
        title.setObjectName("card_title")
        layout.addWidget(title)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border:none; background:rgba(15,23,42,0.6);")

        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setMinimumSize(400, 320)
        self.image_label.setStyleSheet(
            "background:rgba(15,23,42,0.8); border:2px dashed rgba(59,130,246,0.5); border-radius:8px;"
            "color:rgba(148,163,184,0.9); font-size:14px;"
            "font-family:'SimSun','宋体',serif;"
        )
        self.image_label.setText("拖拽图片到此处\n或点击【打开图片】按钮")
        self.image_label.setAcceptDrops(True)
        scroll.setWidget(self.image_label)
        layout.addWidget(scroll)

        # 图片信息
        self.img_info_label = QLabel("")
        self.img_info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.img_info_label.setStyleSheet(
            "font-family:'SimSun','宋体',serif;font-size:12px;color:rgba(148,163,184,0.9);padding:3px;"
        )
        layout.addWidget(self.img_info_label)

        return panel

    def _build_right_panel(self):
        panel = QWidget()
        panel.setObjectName("card")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 8, 10, 10)
        layout.setSpacing(6)

        title = QLabel("识  别  结  果")
        title.setObjectName("card_title")
        layout.addWidget(title)

        tabs = QTabWidget()
        tabs.setStyleSheet("""
            QTabWidget::pane { border:1px solid rgba(59,130,246,0.35); border-radius:0 8px 8px 8px; background:rgba(15,23,42,0.6); }
            QTabBar::tab { font-family:"KaiTi","楷体",serif; font-size:15px; font-weight:bold;
                color:rgba(148,163,184,0.9); background:rgba(15,23,42,0.8); border:1px solid rgba(59,130,246,0.3); border-bottom:none;
                border-radius:6px 6px 0 0; padding:5px 16px; margin-right:3px; }
            QTabBar::tab:selected { background:rgba(30,41,59,0.95); color:#60A5FA; }
        """)

        tabs.addTab(self._build_summary_tab(), "📈  统计摘要")
        tabs.addTab(self._build_detail_tab(), "📋  详细数据")
        tabs.addTab(self._build_chart_tab(), "📊  置信度分布")

        layout.addWidget(tabs)
        return panel

    def _build_summary_tab(self):
        w = QWidget()
        w.setStyleSheet("background:rgba(15,23,42,0.5);")
        outer = QVBoxLayout(w)
        outer.setContentsMargins(12, 12, 12, 12)
        outer.setSpacing(14)

        # 大数字统计卡片行
        stats_row = QHBoxLayout()
        stats_row.setSpacing(12)

        self.stat_total = self._make_stat_card("总检测数", "0", "#60A5FA")
        self.stat_classes = self._make_stat_card("类别数", "0", "#A78BFA")
        self.stat_avg_conf = self._make_stat_card("平均置信度", "0.00", "#67E8F9")
        self.stat_max_conf = self._make_stat_card("最高置信度", "0.00", "#FCA5A5")

        for s in [self.stat_total, self.stat_classes, self.stat_avg_conf, self.stat_max_conf]:
            stats_row.addWidget(s)
        outer.addLayout(stats_row)

        # 类别分布
        cls_title = QLabel("各类别检测数量")
        cls_title.setStyleSheet(
            "font-family:'KaiTi','楷体',serif;font-size:14px;font-weight:bold;"
            "color:#93C5FD;qproperty-alignment:AlignCenter;"
        )
        outer.addWidget(cls_title)

        self.cls_table = QTableWidget()
        self.cls_table.setColumnCount(3)
        self.cls_table.setHorizontalHeaderLabels(["类别", "数量", "占比"])
        self.cls_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.cls_table.setMaximumHeight(220)
        self.cls_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.cls_table.setAlternatingRowColors(True)
        self.cls_table.setStyleSheet("""
            QTableWidget { background:rgba(30,41,59,0.9); border:1px solid rgba(59,130,246,0.35);
                border-radius:8px; gridline-color:rgba(59,130,246,0.2);
                font-family:'SimSun','宋体',serif; font-size:13px; color:#E2E8F0; }
            QTableWidget::item { padding:5px 8px; qproperty-alignment:AlignCenter; }
            QHeaderView::section { font-family:'KaiTi','楷体',serif; font-size:12px;
                font-weight:bold; background:rgba(30,58,95,0.9); color:#93C5FD;
                padding:5px; border:none; border-bottom:2px solid rgba(59,130,246,0.35);
                qproperty-alignment:AlignCenter; }
            QTableWidget::item:alternate { background:rgba(15,23,42,0.5); }
        """)
        outer.addWidget(self.cls_table)
        outer.addStretch()
        return w

    def _make_stat_card(self, label: str, value: str, color: str) -> QWidget:
        card = QWidget()
        card.setStyleSheet(
            f"background:rgba(30,41,59,0.9);border-radius:10px;border:1px solid rgba(59,130,246,0.35);"
        )
        lo = QVBoxLayout(card)
        lo.setContentsMargins(10, 10, 10, 10)
        lo.setSpacing(2)
        val_lbl = QLabel(value)
        val_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        val_lbl.setStyleSheet(
            f"font-family:'KaiTi','楷体',serif;font-size:26px;font-weight:bold;color:{color};"
        )
        lbl = QLabel(label)
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setStyleSheet("font-family:'SimSun','宋体',serif;font-size:11px;color:rgba(148,163,184,0.9);")
        lo.addWidget(val_lbl)
        lo.addWidget(lbl)
        card._val_lbl = val_lbl
        return card

    def _build_detail_tab(self):
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(8, 8, 8, 8)

        self.detail_table = QTableWidget()
        self.detail_table.setColumnCount(8)
        self.detail_table.setHorizontalHeaderLabels(
            ["序号", "类别", "置信度", "X1", "Y1", "X2", "Y2", "面积"]
        )
        self.detail_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.detail_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.detail_table.setAlternatingRowColors(True)
        self.detail_table.verticalHeader().setVisible(False)
        self.detail_table.setStyleSheet("""
            QTableWidget { background:rgba(30,41,59,0.9); border:1px solid rgba(59,130,246,0.35);
                border-radius:8px; gridline-color:rgba(59,130,246,0.2);
                font-family:'SimSun','宋体',serif; font-size:12px; color:#E2E8F0; }
            QTableWidget::item { padding:4px 6px; qproperty-alignment:AlignCenter; }
            QHeaderView::section { font-family:'KaiTi','楷体',serif; font-size:12px;
                font-weight:bold; background:rgba(30,58,95,0.9); color:#93C5FD;
                padding:5px; border:none; border-bottom:2px solid rgba(59,130,246,0.35);
                qproperty-alignment:AlignCenter; }
            QTableWidget::item:alternate { background:rgba(15,23,42,0.5); }
            QTableWidget::item:selected { background:rgba(59,130,246,0.35); }
        """)
        layout.addWidget(self.detail_table)
        return w

    def _build_chart_tab(self):
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(8, 8, 8, 8)

        self.conf_figure = Figure(figsize=(5, 3.5), facecolor="#0f172a")
        self.conf_canvas = FigureCanvas(self.conf_figure)
        layout.addWidget(self.conf_canvas)
        return w

    # ─────────────────────────────────────
    def _open_image(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "选择图片", "",
            "图片文件 (*.jpg *.jpeg *.png *.bmp *.tiff *.webp);;所有文件 (*.*)"
        )
        if path:
            self._load_image(path)

    def _load_image(self, path: str):
        self.current_image_path = path
        pixmap = QPixmap(path)
        if pixmap.isNull():
            self._hide_success_banner()
            self.status_bar.setText(f"⚠️ 无法加载图片：{path}")
            return
        self._show_pixmap(pixmap)
        size = os.path.getsize(path) / 1024
        self.img_info_label.setText(
            f"文件：{os.path.basename(path)}   "
            f"分辨率：{pixmap.width()}×{pixmap.height()}   "
            f"大小：{size:.1f} KB"
        )
        self.detect_btn.setEnabled(True)
        self._hide_success_banner()
        self.status_bar.setText(f"图片已加载：{os.path.basename(path)}，请点击【开始检测】")
        # 重置结果
        self._reset_results()
        self.annotated_arr = None

    def _show_pixmap(self, pixmap: QPixmap):
        label_w = max(self.image_label.width() - 10, 400)
        label_h = max(self.image_label.height() - 10, 320)
        scaled = pixmap.scaled(label_w, label_h,
                               Qt.AspectRatioMode.KeepAspectRatio,
                               Qt.TransformationMode.SmoothTransformation)
        self.image_label.setPixmap(scaled)

    def _start_detect(self):
        if not self.current_image_path:
            return
        cfg = storage.load_config()
        model_path = storage.resolve_path(cfg.get("model_path", ""))
        if not model_path or not os.path.exists(model_path):
            QMessageBox.warning(self, "模型文件不存在",
                                f"请在【模型管理】页面设置正确的模型路径。\n当前路径：{model_path}")
            return

        self.detect_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self._hide_success_banner()
        self.status_bar.setText("正在检测中，请稍候…")

        self.worker = ImageDetectWorker(
            model_path, self.current_image_path,
            cfg.get("conf_threshold", 0.25),
            cfg.get("iou_threshold", 0.70)
        )
        self.worker.finished.connect(self._on_detect_done)
        self.worker.error.connect(self._on_detect_error)
        self.worker.start()

    def _on_detect_done(self, result: dict):
        self.progress_bar.setVisible(False)
        self.detect_btn.setEnabled(True)

        self.annotated_arr = result["annotated_img"]
        self.detected_data = result["parsed"]

        # 显示带框图片
        pixmap = ndarray_to_pixmap(self.annotated_arr)
        self._show_pixmap(pixmap)

        # 填充统计
        self._fill_results(self.detected_data)

        total = self.detected_data["total"]
        avg_conf = self.detected_data["avg_conf"]
        cls_count = len(self.detected_data["class_counts"])
        self._show_success_banner(total, avg_conf, cls_count)

        self.export_img_btn.setEnabled(True)
        self.export_csv_btn.setEnabled(True)

        # 写入历史
        cfg = storage.load_config()
        storage.add_history_record(
            username=self.user_info.get("username", ""),
            detect_type="image",
            source=self.current_image_path,
            model_path=cfg.get("model_path", ""),
            total_detections=total,
            class_counts=self.detected_data["class_counts"],
            conf_threshold=cfg.get("conf_threshold", 0.25)
        )
        self.request_history_refresh.emit()

    def _show_success_banner(self, total: int, avg_conf: float, cls_count: int):
        """显示醒目的检测完成横幅"""
        self.status_bar.setVisible(False)
        self.success_banner.setVisible(True)
        self.success_detail.setText(
            f"共检测到 {total} 个目标  ·  {cls_count} 个类别  ·  平均置信度 {avg_conf:.4f}"
        )

    def _hide_success_banner(self):
        """隐藏成功横幅，恢复普通状态条"""
        self.success_banner.setVisible(False)
        self.status_bar.setVisible(True)

    def _on_detect_error(self, err: str):
        self.progress_bar.setVisible(False)
        self.detect_btn.setEnabled(True)
        self._hide_success_banner()
        self.status_bar.setText(f"❌ 检测出错：{err}")
        QMessageBox.critical(self, "检测失败", f"检测过程中发生错误：\n\n{err}")

    def _fill_results(self, parsed: dict):
        # 统计卡片
        total = parsed["total"]
        cls_count = len(parsed["class_counts"])
        self.stat_total._val_lbl.setText(str(total))
        self.stat_classes._val_lbl.setText(str(cls_count))
        self.stat_avg_conf._val_lbl.setText(f"{parsed['avg_conf']:.4f}")
        self.stat_max_conf._val_lbl.setText(f"{parsed['max_conf']:.4f}")

        # 类别表格
        cls_counts = parsed["class_counts"]
        self.cls_table.setRowCount(len(cls_counts))
        for row, (cls, cnt) in enumerate(
            sorted(cls_counts.items(), key=lambda x: -x[1])
        ):
            pct = f"{cnt / total * 100:.1f}%" if total > 0 else "0%"
            for col, val in enumerate([cls, str(cnt), pct]):
                item = QTableWidgetItem(val)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
                self.cls_table.setItem(row, col, item)

        # 详细表格
        dets = parsed["detections"]
        self.detail_table.setRowCount(len(dets))
        for row, d in enumerate(dets):
            vals = [str(row + 1), d["class_name"], f"{d['confidence']:.4f}",
                    str(d["x1"]), str(d["y1"]), str(d["x2"]), str(d["y2"]),
                    str(d["area"])]
            for col, val in enumerate(vals):
                item = QTableWidgetItem(val)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
                self.detail_table.setItem(row, col, item)

        # 置信度分布图
        self._plot_conf_distribution(dets)

    def _plot_conf_distribution(self, dets: list):
        self.conf_figure.clear()
        ax = self.conf_figure.add_subplot(111)
        ax.set_facecolor("#0f172a")
        self.conf_figure.patch.set_facecolor("#0f172a")

        if not dets:
            ax.text(0.5, 0.5, "暂无检测结果", ha="center", va="center",
                    transform=ax.transAxes, fontsize=12, color="#94A3B8",
                    fontfamily="SimSun")
            self.conf_canvas.draw()
            return

        confs = [d["confidence"] for d in dets]
        cls_names = list(set(d["class_name"] for d in dets))
        colors = ["#3B82F6", "#60A5FA", "#67E8F9", "#FCA5A5",
                  "#FCD34D", "#A78BFA", "#34D399", "#FDE68A", "#F9A8D4", "#6EE7B7"]

        # 按类别分组置信度
        cls_conf = {}
        for d in dets:
            cls_conf.setdefault(d["class_name"], []).append(d["confidence"])

        bins = [i * 0.05 for i in range(21)]
        for i, (cn, clist) in enumerate(cls_conf.items()):
            ax.hist(clist, bins=bins, alpha=0.65, label=cn,
                    color=colors[i % len(colors)], edgecolor="white", linewidth=0.5)

        ax.set_xlabel("置信度", fontsize=10, color="#94A3B8")
        ax.set_ylabel("数量", fontsize=10, color="#94A3B8")
        ax.set_title("置信度分布直方图", fontsize=11, color="#93C5FD", fontweight="bold")
        if len(cls_conf) <= 6:
            ax.legend(fontsize=9, loc="upper left")
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.spines["left"].set_color("#3B82F6")
        ax.spines["bottom"].set_color("#3B82F6")
        ax.tick_params(colors="#94A3B8", labelsize=9)
        ax.set_xlim(0, 1)
        self.conf_figure.tight_layout(pad=1.5)
        self.conf_canvas.draw()

    def _reset_results(self):
        self.detected_data = None
        self.stat_total._val_lbl.setText("0")
        self.stat_classes._val_lbl.setText("0")
        self.stat_avg_conf._val_lbl.setText("0.00")
        self.stat_max_conf._val_lbl.setText("0.00")
        self.cls_table.setRowCount(0)
        self.detail_table.setRowCount(0)
        self.conf_figure.clear()
        self.conf_canvas.draw()
        self.export_img_btn.setEnabled(False)
        self.export_csv_btn.setEnabled(False)

    def _export_image(self):
        if self.annotated_arr is None:
            return
        import cv2
        default_name = f"detection_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
        path, _ = QFileDialog.getSaveFileName(
            self, "导出检测图片", default_name,
            "JPEG图片 (*.jpg);;PNG图片 (*.png);;所有文件 (*)"
        )
        if path:
            cv2.imwrite(path, self.annotated_arr)
            self._hide_success_banner()
            self.status_bar.setText(f"✅ 图片已导出至：{path}")

    def _export_csv(self):
        if not self.detected_data:
            return
        default_name = f"detection_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        path, _ = QFileDialog.getSaveFileName(
            self, "导出检测结果CSV", default_name,
            "CSV文件 (*.csv);;所有文件 (*)"
        )
        if path:
            save_results_csv(self.detected_data["detections"], path)
            self._hide_success_banner()
            self.status_bar.setText(f"✅ CSV已导出至：{path}")

    def _clear(self):
        self.current_image_path = ""
        self.annotated_arr = None
        self.image_label.clear()
        self.image_label.setText("拖拽图片到此处\n或点击【打开图片】按钮")
        self.img_info_label.setText("")
        self.detect_btn.setEnabled(False)
        self._reset_results()
        self._hide_success_banner()
        self.status_bar.setText("已清除，请重新加载图片")

    # 支持拖拽
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        urls = event.mimeData().urls()
        if urls:
            path = urls[0].toLocalFile()
            if path.lower().endswith((".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".webp")):
                self._load_image(path)
