"""
检测历史记录页面，展示图片/视频/摄像头的检测记录与筛选导出。
@作者：Jay
@定制联系vx：Jay8059
@开发日期：2026年
"""

import os
from datetime import datetime

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QFileDialog, QSplitter,
    QTextEdit, QHeaderView, QMessageBox, QComboBox, QLineEdit,
    QSizePolicy, QFrame
)
from PyQt6.QtCore import Qt, pyqtSlot
from PyQt6.QtGui import QColor, QFont

from utils import storage

TYPE_ICON = {"image": "🖼", "video": "🎬", "camera": "📷"}
TYPE_CN = {"image": "图片", "video": "视频", "camera": "摄像头"}


class HistoryPage(QWidget):
    def __init__(self, user_info: dict):
        super().__init__()
        self.user_info = user_info
        self.all_records = []
        self.filtered_records = []
        self._build_ui()
        self.refresh_data()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 12, 16, 12)
        root.setSpacing(10)

        # 工具栏
        root.addWidget(self._build_toolbar())

        # 分割：左表格 + 右详情
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setHandleWidth(6)
        splitter.setStyleSheet("QSplitter::handle { background: rgba(59,130,246,0.5); border-radius: 3px; }")

        splitter.addWidget(self._build_table_panel())
        splitter.addWidget(self._build_detail_panel())
        splitter.setSizes([700, 340])

        root.addWidget(splitter)

        # 状态栏
        self.status_bar = QLabel("共加载 0 条检测记录")
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

        # 类型筛选
        type_lbl = QLabel("类型：")
        type_lbl.setStyleSheet("font-family:'SimSun','宋体',serif;font-size:12px;color:rgba(148,163,184,0.9);")
        self.type_combo = QComboBox()
        self.type_combo.addItems(["全部", "图片", "视频", "摄像头"])
        self.type_combo.setFixedWidth(90)
        self.type_combo.currentIndexChanged.connect(self._apply_filter)

        # 搜索框
        search_lbl = QLabel("搜索：")
        search_lbl.setStyleSheet("font-family:'SimSun','宋体',serif;font-size:12px;color:rgba(148,163,184,0.9);")
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("输入文件名或类别关键词")
        self.search_edit.setFixedWidth(200)
        self.search_edit.setFixedHeight(40)
        self.search_edit.textChanged.connect(self._apply_filter)

        self.refresh_btn = QPushButton("🔄  刷新")
        self.refresh_btn.setObjectName("secondary_btn")
        self.refresh_btn.clicked.connect(self.refresh_data)

        self.export_btn = QPushButton("📥  导出历史CSV")
        self.export_btn.setObjectName("primary_btn")
        self.export_btn.clicked.connect(self._export_history)

        self.clear_btn = QPushButton("🗑  清空历史")
        self.clear_btn.setObjectName("danger_btn")
        self.clear_btn.clicked.connect(self._clear_history)

        for w in [type_lbl, self.type_combo,
                  search_lbl, self.search_edit,
                  self.refresh_btn, self.export_btn, self.clear_btn]:
            layout.addWidget(w)

        layout.addStretch()
        return bar

    def _build_table_panel(self):
        panel = QWidget()
        panel.setObjectName("card")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 8, 10, 10)
        layout.setSpacing(6)

        title = QLabel("检  测  历  史  记  录")
        title.setObjectName("card_title")
        layout.addWidget(title)

        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(
            ["记录ID", "检测时间", "类型", "文件/来源", "模型", "目标总数", "类别分布"]
        )
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.setWordWrap(False)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.Stretch)
        self.table.setStyleSheet("""
            QTableWidget { background:rgba(30,41,59,0.9); border:1px solid rgba(59,130,246,0.35); border-radius:8px;
                gridline-color:rgba(59,130,246,0.2); font-family:'SimSun','宋体',serif;
                font-size:12px; color:#E2E8F0; selection-background-color:rgba(59,130,246,0.35); }
            QTableWidget::item { padding:5px 8px; qproperty-alignment:AlignCenter; }
            QTableWidget::item:alternate { background:rgba(15,23,42,0.5); }
            QHeaderView::section { font-family:'KaiTi','楷体',serif; font-size:12px;
                font-weight:bold; background:rgba(30,58,95,0.9); color:#93C5FD;
                padding:6px; border:none; border-bottom:2px solid rgba(59,130,246,0.35);
                border-right:1px solid rgba(59,130,246,0.25); qproperty-alignment:AlignCenter; }
        """)
        self.table.itemSelectionChanged.connect(self._on_selection_changed)
        layout.addWidget(self.table)
        return panel

    def _build_detail_panel(self):
        panel = QWidget()
        panel.setObjectName("card")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 8, 10, 10)
        layout.setSpacing(8)

        title = QLabel("记  录  详  情")
        title.setObjectName("card_title")
        layout.addWidget(title)

        self.detail_text = QTextEdit()
        self.detail_text.setReadOnly(True)
        self.detail_text.setStyleSheet("""
            QTextEdit { font-family:'SimSun','宋体',serif; font-size:13px; color:#E2E8F0;
                background:rgba(15,23,42,0.8); border:1px solid rgba(59,130,246,0.35); border-radius:8px; padding:10px; }
        """)
        self.detail_text.setPlaceholderText("点击左侧记录查看详情")
        layout.addWidget(self.detail_text)

        return panel

    # ─────────────────────────────────────
    @pyqtSlot()
    def refresh_data(self):
        self.all_records = storage.get_history()
        self._apply_filter()
        self.status_bar.setText(f"共加载 {len(self.all_records)} 条检测记录")

    def _apply_filter(self):
        type_text = self.type_combo.currentText()
        keyword = self.search_edit.text().strip().lower()

        type_map = {"全部": "", "图片": "image", "视频": "video", "摄像头": "camera"}
        type_filter = type_map.get(type_text, "")

        self.filtered_records = []
        for r in self.all_records:
            if type_filter and r.get("type", "") != type_filter:
                continue
            if keyword:
                src = r.get("source", "").lower()
                cls_str = str(r.get("class_counts", {})).lower()
                if keyword not in src and keyword not in cls_str:
                    continue
            self.filtered_records.append(r)

        self._fill_table(self.filtered_records)
        self.status_bar.setText(
            f"共 {len(self.all_records)} 条记录，当前显示 {len(self.filtered_records)} 条"
        )

    def _fill_table(self, records: list):
        self.table.setRowCount(len(records))
        for row, r in enumerate(records):
            ts = r.get("timestamp", "")
            try:
                dt = datetime.fromisoformat(ts)
                ts_str = dt.strftime("%Y-%m-%d %H:%M:%S")
            except Exception:
                ts_str = ts

            dtype = r.get("type", "")
            icon = TYPE_ICON.get(dtype, "❓")
            type_cn = f"{icon} {TYPE_CN.get(dtype, dtype)}"

            src = os.path.basename(r.get("source", ""))
            model = r.get("model", "")
            total = str(r.get("total_detections", 0))
            cls_counts = r.get("class_counts", {})
            cls_str = "  ".join(f"{k}:{v}" for k, v in cls_counts.items()) if cls_counts else "—"

            row_data = [
                r.get("id", ""),
                ts_str, type_cn, src, model, total, cls_str
            ]
            for col, val in enumerate(row_data):
                item = QTableWidgetItem(val)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
                self.table.setItem(row, col, item)

            # 颜色（深空蓝主题行背景）
            if dtype == "image":
                color = QColor("#1e3a5f")
            elif dtype == "video":
                color = QColor("#1e293b")
            else:
                color = QColor("#0f172a")
            if row % 2 == 0:
                for col in range(7):
                    item = self.table.item(row, col)
                    if item:
                        item.setBackground(color)

    def _on_selection_changed(self):
        row = self.table.currentRow()
        if row < 0 or row >= len(self.filtered_records):
            self.detail_text.clear()
            return
        r = self.filtered_records[row]
        self._show_detail(r)

    def _show_detail(self, r: dict):
        ts = r.get("timestamp", "")
        try:
            dt = datetime.fromisoformat(ts)
            ts_str = dt.strftime("%Y年%m月%d日 %H:%M:%S")
        except Exception:
            ts_str = ts

        dtype = r.get("type", "")
        icon = TYPE_ICON.get(dtype, "❓")
        type_cn = TYPE_CN.get(dtype, dtype)
        cls_counts = r.get("class_counts", {})

        lines = [
            f"{'─'*30}",
            f"  记录ID：{r.get('id', '')}",
            f"  检测时间：{ts_str}",
            f"  操作用户：{r.get('username', '')}",
            f"  检测类型：{icon} {type_cn}",
            f"{'─'*30}",
            f"  文件/来源：{r.get('source', '')}",
            f"  使用模型：{r.get('model', '')}",
            f"  置信度阈值：{r.get('conf_threshold', '')}",
            f"{'─'*30}",
            f"  总检测目标数：{r.get('total_detections', 0)}",
            f"  各类别分布：",
        ]
        if cls_counts:
            for k, v in sorted(cls_counts.items(), key=lambda x: -x[1]):
                total = r.get("total_detections", 1)
                pct = v / total * 100 if total > 0 else 0
                lines.append(f"    • {k}：{v} 个（{pct:.1f}%）")
        else:
            lines.append("    （无检测结果）")

        if r.get("result_image_path"):
            lines.append(f"{'─'*30}")
            lines.append(f"  结果图片：{r.get('result_image_path')}")
        if r.get("notes"):
            lines.append(f"  备注：{r.get('notes')}")

        self.detail_text.setPlainText("\n".join(lines))

    def _export_history(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "导出历史记录",
            f"history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            "CSV文件 (*.csv);;所有文件 (*)"
        )
        if path:
            saved = storage.export_history_csv(save_path=path)
            self.status_bar.setText(f"✅ 历史已导出：{saved}")
            QMessageBox.information(self, "导出成功", f"历史记录已导出至：\n{saved}")

    def _clear_history(self):
        reply = QMessageBox.question(
            self, "确认清空",
            "确定要清空所有历史检测记录吗？\n此操作不可撤销！",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            from utils.storage import DATA_DIR, HISTORY_FILE
            if HISTORY_FILE.exists():
                import json
                with open(HISTORY_FILE, "w", encoding="utf-8") as f:
                    json.dump({"records": []}, f)
            self.refresh_data()
            self.detail_text.clear()
            self.status_bar.setText("历史记录已清空")
