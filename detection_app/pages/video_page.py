"""
视频检测页面，支持本地视频 YOLO 检测与进度控制。
@作者：Jay
@定制联系vx：Jay8059
@开发日期：2026年
"""

import os
from datetime import datetime

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFileDialog, QSplitter, QFrame, QProgressBar, QSizePolicy,
    QMessageBox, QSlider, QSpinBox, QCheckBox, QScrollArea
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QPixmap, QImage, QFont

from utils.detector import VideoDetectWorker
from utils import storage


def ndarray_to_pixmap(arr) -> QPixmap:
    import cv2
    rgb = cv2.cvtColor(arr, cv2.COLOR_BGR2RGB)
    h, w, ch = rgb.shape
    img = QImage(rgb.data, w, h, ch * w, QImage.Format.Format_RGB888)
    return QPixmap.fromImage(img)


class VideoPage(QWidget):
    request_history_refresh = pyqtSignal()

    def __init__(self, user_info: dict):
        super().__init__()
        self.user_info = user_info
        self.video_path = ""
        self.worker = None
        self.total_frames = 0
        self.current_frame = 0
        self.last_parsed = {}
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 12, 16, 12)
        root.setSpacing(10)

        # 工具栏
        root.addWidget(self._build_toolbar())

        # 分割视图
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setHandleWidth(6)
        splitter.setStyleSheet("QSplitter::handle { background: rgba(59,130,246,0.5); border-radius: 3px; }")

        splitter.addWidget(self._build_video_panel())
        splitter.addWidget(self._build_result_panel())
        splitter.setSizes([640, 420])

        root.addWidget(splitter)

        # 状态栏
        self.status_bar = QLabel("请点击【打开视频】选择要检测的视频文件")
        self.status_bar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_bar.setStyleSheet(
            "font-family:'SimSun','宋体',serif;font-size:12px;color:#93C5FD;"
            "background:rgba(30,41,59,0.9);border-radius:6px;padding:5px;border:1px solid rgba(59,130,246,0.3);"
        )
        root.addWidget(self.status_bar)

    def _build_toolbar(self):
        bar = QWidget()
        bar.setObjectName("card")
        bar.setMaximumHeight(64)
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(16, 8, 16, 8)
        layout.setSpacing(10)

        self.open_btn = QPushButton("📂  打开视频")
        self.open_btn.setObjectName("primary_btn")
        self.open_btn.clicked.connect(self._open_video)

        self.start_btn = QPushButton("▶  开始检测")
        self.start_btn.setObjectName("success_btn")
        self.start_btn.setEnabled(False)
        self.start_btn.clicked.connect(self._start_detection)

        self.stop_btn = QPushButton("⏹  停止")
        self.stop_btn.setObjectName("danger_btn")
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self._stop_detection)

        self.export_btn = QPushButton("💾  导出帧")
        self.export_btn.setObjectName("secondary_btn")
        self.export_btn.setEnabled(False)
        self.export_btn.clicked.connect(self._export_frame)

        for b in [self.open_btn, self.start_btn, self.stop_btn, self.export_btn]:
            layout.addWidget(b)

        layout.addStretch()

        skip_lbl = QLabel("每N帧检测一次：")
        skip_lbl.setStyleSheet("font-family:'SimSun','宋体',serif;font-size:12px;color:rgba(148,163,184,0.9);")
        self.skip_spin = QSpinBox()
        self.skip_spin.setRange(1, 30)
        self.skip_spin.setValue(2)
        self.skip_spin.setFixedWidth(60)
        self.skip_spin.setStyleSheet(
            "font-family:'SimSun','宋体',serif;font-size:13px;color:#E2E8F0;"
            "background:rgba(15,23,42,0.8);border:2px solid rgba(59,130,246,0.4);border-radius:6px;padding:3px;"
        )
        layout.addWidget(skip_lbl)
        layout.addWidget(self.skip_spin)

        return bar

    def _build_video_panel(self):
        panel = QWidget()
        panel.setObjectName("card")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 8, 10, 10)
        layout.setSpacing(6)

        title = QLabel("视  频  播  放  （含检测标注）")
        title.setObjectName("card_title")
        layout.addWidget(title)

        # 视频显示区
        self.video_label = QLabel()
        self.video_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.video_label.setMinimumSize(500, 360)
        self.video_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.video_label.setStyleSheet(
            "background:#0f172a;border-radius:8px;border:1px solid rgba(59,130,246,0.25);"
            "color:rgba(148,163,184,0.9);font-size:14px;font-family:'SimSun','宋体',serif;"
        )
        self.video_label.setText("请加载视频文件")
        layout.addWidget(self.video_label)

        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setFixedHeight(14)
        self.progress_bar.setTextVisible(True)
        layout.addWidget(self.progress_bar)

        # 视频信息
        self.video_info_label = QLabel("")
        self.video_info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.video_info_label.setStyleSheet(
            "font-family:'SimSun','宋体',serif;font-size:12px;color:rgba(148,163,184,0.9);"
        )
        layout.addWidget(self.video_info_label)

        return panel

    def _build_result_panel(self):
        panel = QWidget()
        panel.setObjectName("card")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 8, 10, 10)
        layout.setSpacing(10)

        title = QLabel("实  时  检  测  结  果")
        title.setObjectName("card_title")
        layout.addWidget(title)

        # 统计卡片
        grid = QWidget()
        grid_layout = QHBoxLayout(grid)
        grid_layout.setContentsMargins(0, 0, 0, 0)
        grid_layout.setSpacing(8)

        self.stat_frame = self._make_mini_stat("当前帧目标", "0", "#60A5FA")
        self.stat_cls_cnt = self._make_mini_stat("类别数", "0", "#A78BFA")
        self.stat_avg_c = self._make_mini_stat("平均置信度", "0.00", "#67E8F9")
        for s in [self.stat_frame, self.stat_cls_cnt, self.stat_avg_c]:
            grid_layout.addWidget(s)
        layout.addWidget(grid)

        # 实时类别统计
        cls_title = QLabel("当前帧各类别目标")
        cls_title.setStyleSheet(
            "font-family:'KaiTi','楷体',serif;font-size:13px;font-weight:bold;"
            "color:#93C5FD;padding:4px 0;"
        )
        cls_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(cls_title)

        self.cls_display = QLabel("—")
        self.cls_display.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.cls_display.setWordWrap(True)
        self.cls_display.setStyleSheet(
            "font-family:'SimSun','宋体',serif;font-size:13px;color:#E2E8F0;"
            "background:rgba(15,23,42,0.8);border-radius:8px;padding:10px;border:1px solid rgba(59,130,246,0.35);"
        )
        self.cls_display.setMinimumHeight(80)
        layout.addWidget(self.cls_display)

        # 累计统计
        accum_title = QLabel("本次检测累计统计")
        accum_title.setStyleSheet(
            "font-family:'KaiTi','楷体',serif;font-size:13px;font-weight:bold;"
            "color:#93C5FD;padding:4px 0;"
        )
        accum_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(accum_title)

        self.accum_label = QLabel("尚未开始检测")
        self.accum_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.accum_label.setWordWrap(True)
        self.accum_label.setStyleSheet(
            "font-family:'SimSun','宋体',serif;font-size:12px;color:#E2E8F0;"
            "background:rgba(15,23,42,0.8);border-radius:8px;padding:10px;border:1px solid rgba(59,130,246,0.35);"
        )
        self.accum_label.setMinimumHeight(80)
        layout.addWidget(self.accum_label)

        layout.addStretch()
        return panel

    def _make_mini_stat(self, label: str, value: str, color: str) -> QWidget:
        card = QWidget()
        card.setStyleSheet(
            "background:rgba(30,41,59,0.9);border-radius:8px;border:1px solid rgba(59,130,246,0.35);"
        )
        lo = QVBoxLayout(card)
        lo.setContentsMargins(6, 8, 6, 8)
        lo.setSpacing(2)
        val_lbl = QLabel(value)
        val_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        val_lbl.setStyleSheet(
            f"font-family:'KaiTi','楷体',serif;font-size:22px;font-weight:bold;color:{color};"
        )
        lbl = QLabel(label)
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setStyleSheet("font-family:'SimSun','宋体',serif;font-size:10px;color:rgba(148,163,184,0.9);")
        lo.addWidget(val_lbl)
        lo.addWidget(lbl)
        card._val_lbl = val_lbl
        return card

    # ─────────────────────────────────────
    def _open_video(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "选择视频文件", "",
            "视频文件 (*.mp4 *.avi *.mov *.mkv *.flv *.wmv);;所有文件 (*.*)"
        )
        if not path:
            return
        import cv2
        cap = cv2.VideoCapture(path)
        if not cap.isOpened():
            QMessageBox.warning(self, "错误", "无法打开视频文件")
            return
        total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        # 读第一帧预览
        ret, frame = cap.read()
        cap.release()

        self.video_path = path
        self.total_frames = total
        self.accum_class_counts = {}

        if ret:
            import cv2 as cv
            pixmap = ndarray_to_pixmap(frame)
            label_w = max(self.video_label.width() - 10, 480)
            label_h = max(self.video_label.height() - 10, 340)
            scaled = pixmap.scaled(label_w, label_h,
                                   Qt.AspectRatioMode.KeepAspectRatio,
                                   Qt.TransformationMode.SmoothTransformation)
            self.video_label.setPixmap(scaled)

        dur = total / fps if fps > 0 else 0
        self.video_info_label.setText(
            f"文件：{os.path.basename(path)}   "
            f"分辨率：{w}×{h}   帧率：{fps:.1f} fps   "
            f"总帧数：{total}   时长：{dur:.1f}s"
        )
        self.progress_bar.setValue(0)
        self.start_btn.setEnabled(True)
        self.status_bar.setText(f"视频已加载：{os.path.basename(path)}，点击【开始检测】")

    def _start_detection(self):
        if not self.video_path:
            return
        cfg = storage.load_config()
        model_path = storage.resolve_path(cfg.get("model_path", ""))
        if not model_path or not os.path.exists(model_path):
            QMessageBox.warning(self, "模型不存在", f"模型文件不存在：\n{model_path}")
            return

        self.accum_class_counts = {}
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.open_btn.setEnabled(False)
        self.export_btn.setEnabled(False)
        self.status_bar.setText("正在检测视频，请稍候…")

        self.worker = VideoDetectWorker(
            model_path, self.video_path,
            cfg.get("conf_threshold", 0.25),
            cfg.get("iou_threshold", 0.70),
            skip=self.skip_spin.value()
        )
        self.worker.frame_ready.connect(self._on_frame)
        self.worker.progress.connect(self._on_progress)
        self.worker.finished.connect(self._on_finished)
        self.worker.error.connect(self._on_error)
        self.worker.start()

    def _stop_detection(self):
        if self.worker:
            self.worker.stop()
        self.stop_btn.setEnabled(False)
        self.status_bar.setText("已停止检测")

    def _on_frame(self, frame, parsed: dict):
        label_w = max(self.video_label.width() - 10, 480)
        label_h = max(self.video_label.height() - 10, 340)
        pixmap = ndarray_to_pixmap(frame)
        scaled = pixmap.scaled(label_w, label_h,
                               Qt.AspectRatioMode.KeepAspectRatio,
                               Qt.TransformationMode.SmoothTransformation)
        self.video_label.setPixmap(scaled)
        self.last_frame = frame

        if parsed:
            self.last_parsed = parsed
            total = parsed["total"]
            cls_counts = parsed["class_counts"]
            avg_c = parsed["avg_conf"]

            self.stat_frame._val_lbl.setText(str(total))
            self.stat_cls_cnt._val_lbl.setText(str(len(cls_counts)))
            self.stat_avg_c._val_lbl.setText(f"{avg_c:.4f}")

            if cls_counts:
                cls_str = "   ".join(f"{k}: {v}" for k, v in cls_counts.items())
            else:
                cls_str = "本帧未检测到目标"
            self.cls_display.setText(cls_str)

            for k, v in cls_counts.items():
                self.accum_class_counts[k] = self.accum_class_counts.get(k, 0) + v

            accum_str = "   ".join(
                f"{k}: {v}" for k, v in sorted(
                    self.accum_class_counts.items(), key=lambda x: -x[1]
                )
            ) or "暂无"
            self.accum_label.setText(accum_str)
            self.export_btn.setEnabled(True)

    def _on_progress(self, current: int, total: int):
        self.current_frame = current
        if total > 0:
            pct = int(current / total * 100)
            self.progress_bar.setValue(pct)
            self.status_bar.setText(
                f"检测进度：{current}/{total} 帧  ({pct}%)"
            )

    def _on_finished(self):
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.open_btn.setEnabled(True)
        self.progress_bar.setValue(100)
        self.status_bar.setText("✅ 视频检测完成！")

        # 写历史
        cfg = storage.load_config()
        storage.add_history_record(
            username=self.user_info.get("username", ""),
            detect_type="video",
            source=self.video_path,
            model_path=cfg.get("model_path", ""),
            total_detections=sum(self.accum_class_counts.values()),
            class_counts=self.accum_class_counts,
            conf_threshold=cfg.get("conf_threshold", 0.25)
        )
        self.request_history_refresh.emit()

    def _on_error(self, err: str):
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.open_btn.setEnabled(True)
        self.status_bar.setText(f"❌ 检测出错：{err}")
        QMessageBox.critical(self, "错误", f"检测过程中发生错误：\n{err}")

    def _export_frame(self):
        if not hasattr(self, "last_frame") or self.last_frame is None:
            return
        import cv2
        default_name = f"frame_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
        path, _ = QFileDialog.getSaveFileName(
            self, "导出当前帧", default_name,
            "JPEG (*.jpg);;PNG (*.png);;所有文件 (*)"
        )
        if path:
            cv2.imwrite(path, self.last_frame)
            self.status_bar.setText(f"✅ 已导出当前帧至：{path}")
