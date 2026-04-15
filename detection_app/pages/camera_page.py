"""
摄像头实时检测页面，支持实时检测与截图保存。
@作者：Jay
@定制联系vx：Jay8059
@开发日期：2026年
"""

import os
from datetime import datetime

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QSplitter, QFileDialog, QSpinBox, QMessageBox, QSizePolicy, QCheckBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPixmap, QImage

from utils.detector import CameraDetectWorker
from utils import storage


def ndarray_to_pixmap(arr) -> QPixmap:
    import cv2
    rgb = cv2.cvtColor(arr, cv2.COLOR_BGR2RGB)
    h, w, ch = rgb.shape
    img = QImage(rgb.data, w, h, ch * w, QImage.Format.Format_RGB888)
    return QPixmap.fromImage(img)


class CameraPage(QWidget):
    request_history_refresh = pyqtSignal()

    def __init__(self, user_info: dict):
        super().__init__()
        self.user_info = user_info
        self.worker = None
        self.snapshot_frame = None
        self.session_class_counts = {}
        self.session_total = 0
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 12, 16, 12)
        root.setSpacing(10)

        root.addWidget(self._build_toolbar())

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setHandleWidth(6)
        splitter.setStyleSheet("QSplitter::handle { background: rgba(59,130,246,0.5); border-radius: 3px; }")

        splitter.addWidget(self._build_camera_panel())
        splitter.addWidget(self._build_result_panel())
        splitter.setSizes([620, 380])

        root.addWidget(splitter)

        self.status_bar = QLabel("请选择摄像头并点击【启动摄像头】")
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

        cam_lbl = QLabel("摄像头：")
        cam_lbl.setStyleSheet("font-family:'SimSun','宋体',serif;font-size:12px;color:rgba(148,163,184,0.9);")
        self.cam_spin = QSpinBox()
        self.cam_spin.setRange(0, 10)
        self.cam_spin.setValue(0)
        self.cam_spin.setFixedWidth(56)
        self.cam_spin.setStyleSheet(
            "font-family:'SimSun','宋体',serif;font-size:13px;color:#E2E8F0;"
            "background:rgba(15,23,42,0.8);border:2px solid rgba(59,130,246,0.4);border-radius:6px;padding:3px;"
        )

        self.start_btn = QPushButton("📷  启动摄像头")
        self.start_btn.setObjectName("primary_btn")
        self.start_btn.clicked.connect(self._start_camera)

        self.stop_btn = QPushButton("⏹  关闭摄像头")
        self.stop_btn.setObjectName("danger_btn")
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self._stop_camera)

        self.detect_toggle = QPushButton("🔍  检测：关")
        self.detect_toggle.setObjectName("secondary_btn")
        self.detect_toggle.setEnabled(False)
        self.detect_toggle.setCheckable(True)
        self.detect_toggle.clicked.connect(self._toggle_detect)

        self.snapshot_btn = QPushButton("📸  截图保存")
        self.snapshot_btn.setObjectName("secondary_btn")
        self.snapshot_btn.setEnabled(False)
        self.snapshot_btn.clicked.connect(self._take_snapshot)

        for w in [cam_lbl, self.cam_spin, self.start_btn,
                  self.stop_btn, self.detect_toggle, self.snapshot_btn]:
            layout.addWidget(w)

        layout.addStretch()

        freq_lbl = QLabel("每N帧检测：")
        freq_lbl.setStyleSheet("font-family:'SimSun','宋体',serif;font-size:12px;color:rgba(148,163,184,0.9);")
        self.freq_spin = QSpinBox()
        self.freq_spin.setRange(1, 30)
        self.freq_spin.setValue(3)
        self.freq_spin.setFixedWidth(56)
        self.freq_spin.setStyleSheet(
            "font-family:'SimSun','宋体',serif;font-size:13px;color:#E2E8F0;"
            "background:rgba(15,23,42,0.8);border:2px solid rgba(59,130,246,0.4);border-radius:6px;padding:3px;"
        )
        layout.addWidget(freq_lbl)
        layout.addWidget(self.freq_spin)

        return bar

    def _build_camera_panel(self):
        panel = QWidget()
        panel.setObjectName("card")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 8, 10, 10)
        layout.setSpacing(6)

        title = QLabel("实  时  摄  像  头  画  面")
        title.setObjectName("card_title")
        layout.addWidget(title)

        self.camera_label = QLabel()
        self.camera_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.camera_label.setMinimumSize(500, 380)
        self.camera_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.camera_label.setStyleSheet(
            "background:#0f172a;border-radius:8px;border:1px solid rgba(59,130,246,0.25);"
            "color:rgba(148,163,184,0.9);font-size:16px;font-family:'SimSun','宋体',serif;"
        )
        self.camera_label.setText("摄像头未启动")
        layout.addWidget(self.camera_label)

        self.fps_label = QLabel("")
        self.fps_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.fps_label.setStyleSheet(
            "font-family:'SimSun','宋体',serif;font-size:11px;color:rgba(148,163,184,0.9);"
        )
        layout.addWidget(self.fps_label)

        return panel

    def _build_result_panel(self):
        panel = QWidget()
        panel.setObjectName("card")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 8, 10, 10)
        layout.setSpacing(10)

        title = QLabel("实  时  检  测  统  计")
        title.setObjectName("card_title")
        layout.addWidget(title)

        # 实时统计卡片
        row1 = QHBoxLayout()
        row1.setSpacing(8)
        self.stat_det = self._make_stat("当前目标数", "0", "#60A5FA")
        self.stat_cls = self._make_stat("类别数", "0", "#A78BFA")
        self.stat_conf = self._make_stat("置信度", "0.00", "#67E8F9")
        for s in [self.stat_det, self.stat_cls, self.stat_conf]:
            row1.addWidget(s)
        layout.addLayout(row1)

        row2 = QHBoxLayout()
        row2.setSpacing(8)
        self.stat_total = self._make_stat("累计检测", "0", "#FCA5A5")
        self.stat_snap = self._make_stat("截图数", "0", "#FCD34D")
        for s in [self.stat_total, self.stat_snap]:
            row2.addWidget(s)
        layout.addLayout(row2)

        # 当前帧类别
        cls_title = QLabel("当前帧目标分布")
        cls_title.setStyleSheet(
            "font-family:'KaiTi','楷体',serif;font-size:13px;font-weight:bold;"
            "color:#93C5FD;padding:4px 0;"
        )
        cls_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(cls_title)

        self.cls_live = QLabel("—")
        self.cls_live.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.cls_live.setWordWrap(True)
        self.cls_live.setStyleSheet(
            "font-family:'SimSun','宋体',serif;font-size:13px;color:#E2E8F0;"
            "background:rgba(15,23,42,0.8);border-radius:8px;padding:10px;border:1px solid rgba(59,130,246,0.35);"
        )
        self.cls_live.setMinimumHeight(70)
        layout.addWidget(self.cls_live)

        # 本次会话累计
        sess_title = QLabel("本次会话累计")
        sess_title.setStyleSheet(
            "font-family:'KaiTi','楷体',serif;font-size:13px;font-weight:bold;"
            "color:#93C5FD;padding:4px 0;"
        )
        sess_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(sess_title)

        self.session_label = QLabel("—")
        self.session_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.session_label.setWordWrap(True)
        self.session_label.setStyleSheet(
            "font-family:'SimSun','宋体',serif;font-size:12px;color:#E2E8F0;"
            "background:rgba(15,23,42,0.8);border-radius:8px;padding:10px;border:1px solid rgba(59,130,246,0.35);"
        )
        self.session_label.setMinimumHeight(70)
        layout.addWidget(self.session_label)

        layout.addStretch()

        # 保存会话记录
        self.save_session_btn = QPushButton("💾  保存本次会话到历史")
        self.save_session_btn.setObjectName("secondary_btn")
        self.save_session_btn.setEnabled(False)
        self.save_session_btn.clicked.connect(self._save_session)
        layout.addWidget(self.save_session_btn)

        return panel

    def _make_stat(self, label: str, value: str, color: str) -> QWidget:
        card = QWidget()
        card.setStyleSheet("background:rgba(30,41,59,0.9);border-radius:8px;border:1px solid rgba(59,130,246,0.35);")
        lo = QVBoxLayout(card)
        lo.setContentsMargins(6, 8, 6, 8)
        lo.setSpacing(2)
        val_lbl = QLabel(value)
        val_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        val_lbl.setStyleSheet(
            f"font-family:'KaiTi','楷体',serif;font-size:20px;font-weight:bold;color:{color};"
        )
        lbl = QLabel(label)
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setStyleSheet("font-family:'SimSun','宋体',serif;font-size:10px;color:rgba(148,163,184,0.9);")
        lo.addWidget(val_lbl)
        lo.addWidget(lbl)
        card._val_lbl = val_lbl
        return card

    # ─────────────────────────────────────
    def _start_camera(self):
        cfg = storage.load_config()
        model_path = storage.resolve_path(cfg.get("model_path", ""))
        if not model_path or not os.path.exists(model_path):
            QMessageBox.warning(self, "模型不存在", f"模型文件不存在：\n{model_path}")
            return

        cam_idx = self.cam_spin.value()
        self.session_class_counts = {}
        self.session_total = 0
        self.snapshot_count = 0

        self.worker = CameraDetectWorker(
            model_path, cam_idx,
            cfg.get("conf_threshold", 0.25),
            cfg.get("iou_threshold", 0.70),
            detect_every=self.freq_spin.value()
        )
        self.worker.set_detect(False)
        self.worker.frame_ready.connect(self._on_frame)
        self.worker.error.connect(self._on_error)
        self.worker.start()

        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.detect_toggle.setEnabled(True)
        self.snapshot_btn.setEnabled(True)
        self.status_bar.setText(f"✅ 摄像头 {cam_idx} 已启动，可开启实时检测")

    def _stop_camera(self):
        if self.worker:
            self.worker.stop()
            self.worker.wait()
            self.worker = None
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.detect_toggle.setEnabled(False)
        self.detect_toggle.setChecked(False)
        self.detect_toggle.setText("🔍  检测：关")
        self.snapshot_btn.setEnabled(False)
        self.camera_label.setPixmap(QPixmap())
        self.camera_label.setText("摄像头已关闭")
        self.status_bar.setText("摄像头已关闭")

        if self.session_total > 0:
            self.save_session_btn.setEnabled(True)

    def _toggle_detect(self, checked: bool):
        if self.worker:
            self.worker.set_detect(checked)
        if checked:
            self.detect_toggle.setText("🔍  检测：开")
            self.status_bar.setText("实时检测已开启")
        else:
            self.detect_toggle.setText("🔍  检测：关")
            self.status_bar.setText("实时检测已关闭（仅预览）")

    def _on_frame(self, frame, parsed: dict):
        label_w = max(self.camera_label.width() - 10, 480)
        label_h = max(self.camera_label.height() - 10, 360)
        pixmap = ndarray_to_pixmap(frame)
        scaled = pixmap.scaled(label_w, label_h,
                               Qt.AspectRatioMode.KeepAspectRatio,
                               Qt.TransformationMode.SmoothTransformation)
        self.camera_label.setPixmap(scaled)
        self.snapshot_frame = frame

        if parsed:
            total = parsed["total"]
            cls_counts = parsed["class_counts"]
            avg_c = parsed["avg_conf"]

            self.stat_det._val_lbl.setText(str(total))
            self.stat_cls._val_lbl.setText(str(len(cls_counts)))
            self.stat_conf._val_lbl.setText(f"{avg_c:.4f}")

            self.session_total += total
            self.stat_total._val_lbl.setText(str(self.session_total))

            if cls_counts:
                cls_str = "   ".join(f"{k}: {v}" for k, v in cls_counts.items())
                self.cls_live.setText(cls_str)
            else:
                self.cls_live.setText("本帧无目标")

            for k, v in cls_counts.items():
                self.session_class_counts[k] = self.session_class_counts.get(k, 0) + v

            if self.session_class_counts:
                sess_str = "   ".join(
                    f"{k}: {v}" for k, v in sorted(
                        self.session_class_counts.items(), key=lambda x: -x[1]
                    )
                )
                self.session_label.setText(sess_str)

    def _on_error(self, err: str):
        self._stop_camera()
        QMessageBox.critical(self, "摄像头错误", f"摄像头发生错误：\n{err}")

    def _take_snapshot(self):
        if self.snapshot_frame is None:
            return
        import cv2
        save_dir = os.path.join(os.path.expanduser("~"), "Pictures", "DroneDetection")
        os.makedirs(save_dir, exist_ok=True)
        fname = f"snapshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
        path = os.path.join(save_dir, fname)
        cv2.imwrite(path, self.snapshot_frame)
        if not hasattr(self, "snapshot_count"):
            self.snapshot_count = 0
        self.snapshot_count += 1
        self.stat_snap._val_lbl.setText(str(self.snapshot_count))
        self.status_bar.setText(f"📸 截图已保存：{path}")

    def _save_session(self):
        cfg = storage.load_config()
        storage.add_history_record(
            username=self.user_info.get("username", ""),
            detect_type="camera",
            source=f"摄像头 {self.cam_spin.value()}",
            model_path=cfg.get("model_path", ""),
            total_detections=self.session_total,
            class_counts=self.session_class_counts,
            conf_threshold=cfg.get("conf_threshold", 0.25)
        )
        self.save_session_btn.setEnabled(False)
        self.status_bar.setText("✅ 已保存到历史记录")
        self.request_history_refresh.emit()
