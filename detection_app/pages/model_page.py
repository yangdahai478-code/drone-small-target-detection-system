"""
模型管理页面，模型路径加载、置信度/IOU 参数配置。
@作者：Jay
@定制联系vx：Jay8059
@开发日期：2026年
"""

import os
from datetime import datetime

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFileDialog, QLineEdit, QDoubleSpinBox, QSpinBox,
    QMessageBox, QFrame, QGridLayout, QTextEdit, QSizePolicy,
    QProgressBar
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal

from utils.detector import ModelLoadWorker
from utils import storage


class ModelPage(QWidget):
    model_changed = pyqtSignal(str)

    def __init__(self, user_info: dict):
        super().__init__()
        self.user_info = user_info
        self.load_worker = None
        self._build_ui()
        self._load_current_config()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 12, 16, 12)
        root.setSpacing(14)

        # 顶部状态栏
        self.status_bar = QLabel("请确认并设置模型路径")
        self.status_bar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_bar.setStyleSheet(
            "font-family:'SimSun','宋体',serif;font-size:12px;color:#93C5FD;"
            "background:rgba(30,41,59,0.9);border-radius:6px;padding:5px;border:1px solid rgba(59,130,246,0.3);"
        )
        root.addWidget(self.status_bar)

        # 模型路径卡片
        root.addWidget(self._build_model_card())

        # 参数配置卡片
        root.addWidget(self._build_params_card())

        # 模型信息卡片
        root.addWidget(self._build_info_card())

        root.addStretch()

    def _build_model_card(self):
        card = QWidget()
        card.setObjectName("card")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 10, 16, 14)
        layout.setSpacing(10)

        title = QLabel("模  型  文  件  设  置")
        title.setObjectName("card_title")
        layout.addWidget(title)

        # 当前模型路径
        row = QHBoxLayout()
        row.setSpacing(8)

        lbl = QLabel("当前模型路径：")
        lbl.setStyleSheet("font-family:'SimSun','宋体',serif;font-size:13px;color:rgba(148,163,184,0.9);")
        lbl.setFixedWidth(110)

        self.model_path_edit = QLineEdit()
        self.model_path_edit.setReadOnly(True)
        self.model_path_edit.setPlaceholderText("请选择 .pt 模型文件")
        self.model_path_edit.setFixedHeight(36)
        self.model_path_edit.setStyleSheet(
            "font-family:'SimSun','宋体',serif;font-size:12px;color:#E2E8F0;"
            "background:rgba(15,23,42,0.8);border:2px solid rgba(59,130,246,0.4);border-radius:8px;padding:4px 10px;"
        )

        browse_btn = QPushButton("📂  浏览")
        browse_btn.setObjectName("secondary_btn")
        browse_btn.setFixedHeight(36)
        browse_btn.clicked.connect(self._browse_model)

        row.addWidget(lbl)
        row.addWidget(self.model_path_edit)
        row.addWidget(browse_btn)
        layout.addLayout(row)

        # 状态行
        status_row = QHBoxLayout()
        self.model_status_lbl = QLabel("⚪ 尚未验证")
        self.model_status_lbl.setStyleSheet(
            "font-family:'SimSun','宋体',serif;font-size:13px;color:rgba(148,163,184,0.9);"
        )
        status_row.addWidget(self.model_status_lbl)
        status_row.addStretch()

        self.load_btn = QPushButton("⚙️  验证并加载模型")
        self.load_btn.setObjectName("primary_btn")
        self.load_btn.clicked.connect(self._load_model)

        self.progress = QProgressBar()
        self.progress.setRange(0, 0)
        self.progress.setFixedWidth(120)
        self.progress.setFixedHeight(14)
        self.progress.setVisible(False)

        status_row.addWidget(self.progress)
        status_row.addWidget(self.load_btn)
        layout.addLayout(status_row)

        return card

    def _build_params_card(self):
        card = QWidget()
        card.setObjectName("card")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 10, 16, 14)
        layout.setSpacing(10)

        title = QLabel("检  测  参  数  设  置")
        title.setObjectName("card_title")
        layout.addWidget(title)

        grid = QGridLayout()
        grid.setSpacing(12)
        grid.setColumnStretch(1, 1)
        grid.setColumnStretch(3, 1)

        # 置信度
        conf_lbl = QLabel("置信度阈值 (conf)：")
        conf_lbl.setStyleSheet("font-family:'SimSun','宋体',serif;font-size:13px;color:rgba(148,163,184,0.9);")
        self.conf_spin = QDoubleSpinBox()
        self.conf_spin.setRange(0.01, 0.99)
        self.conf_spin.setSingleStep(0.05)
        self.conf_spin.setDecimals(2)
        self.conf_spin.setFixedHeight(36)
        self.conf_spin.setStyleSheet(
            "font-family:'SimSun','宋体',serif;font-size:13px;color:#E2E8F0;"
            "background:rgba(15,23,42,0.8);border:2px solid rgba(59,130,246,0.4);border-radius:8px;padding:4px;"
        )

        # IoU
        iou_lbl = QLabel("IoU 阈值 (iou)：")
        iou_lbl.setStyleSheet("font-family:'SimSun','宋体',serif;font-size:13px;color:rgba(148,163,184,0.9);")
        self.iou_spin = QDoubleSpinBox()
        self.iou_spin.setRange(0.01, 0.99)
        self.iou_spin.setSingleStep(0.05)
        self.iou_spin.setDecimals(2)
        self.iou_spin.setFixedHeight(36)
        self.iou_spin.setStyleSheet(
            "font-family:'SimSun','宋体',serif;font-size:13px;color:#E2E8F0;"
            "background:rgba(15,23,42,0.8);border:2px solid rgba(59,130,246,0.4);border-radius:8px;padding:4px;"
        )

        # 最大检测数
        maxdet_lbl = QLabel("最大检测数 (max_det)：")
        maxdet_lbl.setStyleSheet("font-family:'SimSun','宋体',serif;font-size:13px;color:rgba(148,163,184,0.9);")
        self.maxdet_spin = QSpinBox()
        self.maxdet_spin.setRange(1, 1000)
        self.maxdet_spin.setSingleStep(50)
        self.maxdet_spin.setFixedHeight(36)
        self.maxdet_spin.setStyleSheet(
            "font-family:'SimSun','宋体',serif;font-size:13px;color:#E2E8F0;"
            "background:rgba(15,23,42,0.8);border:2px solid rgba(59,130,246,0.4);border-radius:8px;padding:4px;"
        )

        grid.addWidget(conf_lbl, 0, 0)
        grid.addWidget(self.conf_spin, 0, 1)
        grid.addWidget(iou_lbl, 0, 2)
        grid.addWidget(self.iou_spin, 0, 3)
        grid.addWidget(maxdet_lbl, 1, 0)
        grid.addWidget(self.maxdet_spin, 1, 1)

        layout.addLayout(grid)

        # 参数说明
        hints = [
            "• 置信度阈值：检测目标的最低置信度，越高则检测越严格（漏检更多），越低则检测越宽松（误检更多）",
            "• IoU 阈值：NMS去重阈值，越高保留更多重叠框，越低则只保留最优框",
            "• 最大检测数：单张图片/帧最多保留的检测框数量"
        ]
        hint_lbl = QLabel("\n".join(hints))
        hint_lbl.setStyleSheet(
            "font-family:'SimSun','宋体',serif;font-size:11px;color:rgba(148,163,184,0.8);"
            "padding:4px 0;line-height:1.6;"
        )
        hint_lbl.setWordWrap(True)
        layout.addWidget(hint_lbl)

        # 保存按钮
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        save_btn = QPushButton("💾  保存设置")
        save_btn.setObjectName("primary_btn")
        save_btn.clicked.connect(self._save_params)
        btn_row.addWidget(save_btn)
        layout.addLayout(btn_row)

        return card

    def _build_info_card(self):
        card = QWidget()
        card.setObjectName("card")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 10, 16, 14)
        layout.setSpacing(8)

        title = QLabel("模  型  信  息  &  类  别  说  明")
        title.setObjectName("card_title")
        layout.addWidget(title)

        info_text = """
  【模型】YOLOv11 (best.pt)

  【数据集】VisDrone 2019  （训练集 6471 张 / 验证集 548 张 / 测试集 1610 张）

  【优化器】SGD     【输入尺寸】640×640

  【检测类别（共 10 类）】
     0 - 行人 (pedestrian)       1 - 人群 (people)
     2 - 自行车 (bicycle)        3 - 小汽车 (car)
     4 - 面包车 (van)            5 - 卡车 (truck)
     6 - 三轮车 (tricycle)       7 - 带篷三轮车 (awning-tricycle)
     8 - 公交车 (bus)            9 - 摩托车 (motor)
        """
        info_lbl = QTextEdit()
        info_lbl.setReadOnly(True)
        info_lbl.setPlainText(info_text)
        info_lbl.setMaximumHeight(220)
        info_lbl.setStyleSheet(
            "font-family:'SimSun','宋体',serif;font-size:13px;color:#E2E8F0;"
            "background:rgba(15,23,42,0.8);border:1px solid rgba(59,130,246,0.35);border-radius:8px;padding:6px;"
            "line-height:1.8;"
        )
        layout.addWidget(info_lbl)

        return card

    # ─────────────────────────────────────
    def _load_current_config(self):
        cfg = storage.load_config()
        self.model_path_edit.setText(cfg.get("model_path", ""))
        self.conf_spin.setValue(cfg.get("conf_threshold", 0.25))
        self.iou_spin.setValue(cfg.get("iou_threshold", 0.70))
        self.maxdet_spin.setValue(cfg.get("max_det", 300))
        model_path = storage.resolve_path(cfg.get("model_path", ""))
        if model_path and os.path.exists(model_path):
            self.model_status_lbl.setText("✅ 模型文件存在（未加载）")
            self.model_status_lbl.setStyleSheet(
                "font-family:'SimSun','宋体',serif;font-size:13px;color:#67E8F9;"
            )
        else:
            self.model_status_lbl.setText("⚠️ 模型文件不存在，请重新选择")
            self.model_status_lbl.setStyleSheet(
                "font-family:'SimSun','宋体',serif;font-size:13px;color:#FCA5A5;"
            )

    def _browse_model(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "选择模型文件", "",
            "PyTorch模型 (*.pt *.pth);;所有文件 (*.*)"
        )
        if path:
            self.model_path_edit.setText(path)
            self.model_status_lbl.setText("⚪ 已选择文件，点击【验证并加载】")
            self.model_status_lbl.setStyleSheet(
                "font-family:'SimSun','宋体',serif;font-size:13px;color:rgba(148,163,184,0.9);"
            )
            # 自动保存路径
            cfg = storage.load_config()
            cfg["model_path"] = path
            storage.save_config(cfg)

    def _load_model(self):
        path = self.model_path_edit.text().strip()
        if not path:
            QMessageBox.warning(self, "提示", "请先选择模型文件")
            return
        path_resolved = storage.resolve_path(path)
        if not os.path.exists(path_resolved):
            QMessageBox.warning(self, "文件不存在", f"找不到文件：\n{path}")
            return

        self.load_btn.setEnabled(False)
        self.progress.setVisible(True)
        self.model_status_lbl.setText("⏳ 正在加载模型…")
        self.model_status_lbl.setStyleSheet(
            "font-family:'SimSun','宋体',serif;font-size:13px;color:#FCD34D;"
        )

        self.load_worker = ModelLoadWorker(path_resolved)
        self.load_worker.finished.connect(self._on_model_loaded)
        self.load_worker.start()

    def _on_model_loaded(self, success: bool, msg: str):
        self.load_btn.setEnabled(True)
        self.progress.setVisible(False)
        if success:
            self.model_status_lbl.setText(f"✅ {msg}")
            self.model_status_lbl.setStyleSheet(
                "font-family:'SimSun','宋体',serif;font-size:13px;color:#67E8F9;"
            )
            self.status_bar.setText(f"✅ 模型加载成功：{self.model_path_edit.text()}")
            self.model_changed.emit(self.model_path_edit.text())
        else:
            self.model_status_lbl.setText(f"❌ {msg}")
            self.model_status_lbl.setStyleSheet(
                "font-family:'SimSun','宋体',serif;font-size:13px;color:#FCA5A5;"
            )
            QMessageBox.critical(self, "加载失败", msg)

    def _save_params(self):
        cfg = storage.load_config()
        cfg["model_path"] = self.model_path_edit.text().strip()
        cfg["conf_threshold"] = self.conf_spin.value()
        cfg["iou_threshold"] = self.iou_spin.value()
        cfg["max_det"] = self.maxdet_spin.value()
        storage.save_config(cfg)
        self.status_bar.setText("✅ 参数设置已保存")
        QMessageBox.information(self, "保存成功", "检测参数已保存，下次检测时生效。")
