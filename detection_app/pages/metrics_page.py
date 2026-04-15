"""
指标展示页面，训练曲线、混淆矩阵等训练结果可视化。
@作者：Jay
@定制联系vx：Jay8059
@开发日期：2026年
"""

import os

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTabWidget, QScrollArea, QGridLayout, QSizePolicy, QFrame
)
from PyQt6.QtCore import Qt

import matplotlib
matplotlib.use("QtAgg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import numpy as np

from utils import storage

plt.rcParams["font.sans-serif"] = ["SimSun", "宋体", "Microsoft YaHei", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False

# ── 与主题一致的暗色图表配色 ──────────────────────────────────────────
C = {
    "fig_bg":     "#0b1120",
    "ax_bg":      "#0f172a",
    "grid":       "#1e2d45",
    "spine":      "#1e3a5f",
    "text":       "#94a3b8",
    "title":      "#93C5FD",
    "blue":       "#3B82F6",
    "cyan":       "#22D3EE",
    "purple":     "#A78BFA",
    "teal":       "#34D399",
    "rose":       "#F87171",
    "amber":      "#FBBF24",
    "indigo":     "#818CF8",
    "pink":       "#F472B6",
}

TAB_STYLE = """
QTabWidget::pane {
    background: transparent;
    border: none;
}
QTabBar::tab {
    font-family: "KaiTi","楷体",serif;
    font-size: 14px;
    font-weight: bold;
    color: rgba(148,163,184,0.8);
    background: rgba(15,23,42,0.6);
    border: 1px solid rgba(59,130,246,0.25);
    border-bottom: none;
    border-radius: 8px 8px 0 0;
    padding: 8px 20px;
    margin-right: 4px;
}
QTabBar::tab:selected {
    color: #93C5FD;
    background: rgba(30,58,95,0.8);
    border: 1px solid rgba(59,130,246,0.6);
    border-bottom: none;
    border-top: 2px solid #3B82F6;
}
QTabBar::tab:hover:!selected {
    background: rgba(30,41,59,0.8);
    color: #60A5FA;
}
"""

SCROLL_STYLE = "border:none; background:transparent;"
CONTAINER_STYLE = "background:transparent;"

CARD_BASE = (
    "border-radius:14px;"
    "border:1px solid rgba(59,130,246,0.3);"
)


def _dark_card_style(accent: str) -> str:
    return (
        f"background:rgba(15,23,42,0.85);"
        f"border-radius:14px;"
        f"border:1px solid rgba(59,130,246,0.25);"
        f"border-top:2px solid {accent};"
    )


def _make_fig(w=5.2, h=3.4) -> tuple:
    fig = Figure(figsize=(w, h), facecolor=C["fig_bg"])
    canvas = FigureCanvas(fig)
    canvas.setStyleSheet("background:transparent;border:none;")
    return fig, canvas


def _style_ax(ax, xlabel="Epoch", ylabel=""):
    ax.set_facecolor(C["ax_bg"])
    ax.set_xlabel(xlabel, fontsize=9, color=C["text"], labelpad=6)
    ax.set_ylabel(ylabel, fontsize=9, color=C["text"], labelpad=6)
    for sp in ax.spines.values():
        sp.set_color(C["spine"])
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.tick_params(colors=C["text"], labelsize=8, length=3)
    ax.grid(True, linestyle="--", alpha=0.25, color=C["grid"], linewidth=0.7)


def _fill_under(ax, x, y, color, alpha=0.12):
    ax.fill_between(x, y, alpha=alpha, color=color)


class MetricsPage(QWidget):
    def __init__(self, user_info: dict):
        super().__init__()
        self.user_info = user_info
        self.metrics_dir = storage.resolve_path(storage.load_config().get("metrics_dir", ""))
        self.csv_data = None
        self.setStyleSheet("background:transparent;")
        self._build_ui()
        self._load_data()

    # ─────────────────────────── 主体 UI ──────────────────────────────
    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(14, 10, 14, 10)
        root.setSpacing(10)
        root.addWidget(self._build_toolbar())

        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(TAB_STYLE)
        self.tabs.addTab(self._build_curve_tab(),  "📈  训练曲线")
        self.tabs.addTab(self._build_metric_tab(), "🎯  指标汇总")
        root.addWidget(self.tabs)

    # ── 工具栏 ──
    def _build_toolbar(self):
        bar = QWidget()
        bar.setStyleSheet(
            "background:rgba(15,23,42,0.85);border-radius:10px;"
            "border:1px solid rgba(59,130,246,0.3);"
        )
        bar.setMaximumHeight(52)
        lay = QHBoxLayout(bar)
        lay.setContentsMargins(16, 8, 14, 8)
        lay.setSpacing(10)

        dot = QLabel("●")
        dot.setStyleSheet("color:#3B82F6;font-size:10px;")
        lbl = QLabel("训练结果可视化  ·  数据来源：results.csv 及训练图表")
        lbl.setStyleSheet(
            "font-family:'SimSun','宋体',serif;font-size:12px;"
            "color:rgba(148,163,184,0.85);background:transparent;border:none;"
        )
        lay.addWidget(dot)
        lay.addWidget(lbl)
        lay.addStretch()

        btn = QPushButton("⟳  刷新数据")
        btn.setObjectName("secondary_btn")
        btn.setFixedHeight(32)
        btn.clicked.connect(self._load_data)
        lay.addWidget(btn)
        return bar

    # ── 训练曲线 Tab ──
    def _build_curve_tab(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(SCROLL_STYLE)

        container = QWidget()
        container.setStyleSheet(CONTAINER_STYLE)
        grid = QGridLayout(container)
        grid.setContentsMargins(12, 12, 12, 12)
        grid.setSpacing(14)

        self.curve_figs = {}
        specs = [
            ("train_loss", "训练损失",     0, 0),
            ("val_loss",   "验证损失",     0, 1),
            ("map50",      "mAP 指标",     1, 0),
            ("pr_curve",   "精确率 & 召回率", 1, 1),
        ]
        accents = [C["blue"], C["cyan"], C["purple"], C["teal"]]
        for (key, ttl, row, col), accent in zip(specs, accents):
            fig, canvas = _make_fig(5.2, 3.4)
            canvas.setMinimumSize(400, 250)
            wrapper = self._chart_card(ttl, canvas, accent)
            grid.addWidget(wrapper, row, col)
            self.curve_figs[key] = (fig, canvas)

        scroll.setWidget(container)
        return scroll

    # ── 指标汇总 Tab ──
    def _build_metric_tab(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(SCROLL_STYLE)

        container = QWidget()
        container.setStyleSheet(CONTAINER_STYLE)
        vlay = QVBoxLayout(container)
        vlay.setContentsMargins(14, 12, 14, 12)
        vlay.setSpacing(14)

        # 关键指标
        self.big_stats = {}
        kpi_specs = [
            ("mAP50",     "mAP@0.5",      C["blue"],   "↑ 最优轮次"),
            ("mAP5095",   "mAP@0.5:0.95", C["purple"], "↑ 最优轮次"),
            ("precision", "精 确 率",      C["teal"],   "↑ 最优轮次"),
            ("recall",    "召 回 率",      C["rose"],   "↑ 最优轮次"),
        ]
        kpi_row = QHBoxLayout()
        kpi_row.setSpacing(12)
        for key, label, color, sub in kpi_specs:
            card, vl = self._kpi_card(label, "—", color, sub)
            kpi_row.addWidget(card)
            self.big_stats[key] = vl
        vlay.addLayout(kpi_row)

        # 损失指标
        self.loss_stats = {}
        loss_specs = [
            ("train_box", "Train Box Loss", C["blue"]),
            ("train_cls", "Train Cls Loss", C["amber"]),
            ("train_dfl", "Train DFL Loss", C["indigo"]),
            ("val_box",   "Val  Box Loss",  C["pink"]),
        ]
        loss_row = QHBoxLayout()
        loss_row.setSpacing(12)
        for key, label, color in loss_specs:
            card, vl = self._mini_stat_card(label, "—", color)
            loss_row.addWidget(card)
            self.loss_stats[key] = vl
        vlay.addLayout(loss_row)

        # 总览图
        overview_fig, overview_canvas = _make_fig(10, 3.8)
        overview_canvas.setMinimumHeight(240)
        wrapper = self._chart_card("关键指标收敛总览", overview_canvas, C["blue"])
        vlay.addWidget(wrapper)
        self.best_fig = overview_fig
        self.best_canvas = overview_canvas

        vlay.addStretch()
        scroll.setWidget(container)
        return scroll

    # ────────────────── 卡片组件 ──────────────────────────────────────
    def _chart_card(self, title: str, canvas, accent: str) -> QWidget:
        wrapper = QWidget()
        wrapper.setStyleSheet(
            f"background:rgba(15,23,42,0.88);"
            f"border-radius:14px;"
            f"border:1px solid rgba(59,130,246,0.22);"
            f"border-top:2px solid {accent};"
        )
        lay = QVBoxLayout(wrapper)
        lay.setContentsMargins(10, 8, 10, 10)
        lay.setSpacing(4)

        title_w = QWidget()
        title_w.setStyleSheet("background:transparent;border:none;")
        title_lay = QHBoxLayout(title_w)
        title_lay.setContentsMargins(0, 0, 0, 0)
        title_lay.setSpacing(6)

        dot = QLabel("▍")
        dot.setStyleSheet(f"color:{accent};font-size:14px;background:transparent;border:none;")
        lbl = QLabel(title)
        lbl.setStyleSheet(
            f"font-family:'KaiTi','楷体',serif;font-size:13px;font-weight:bold;"
            f"color:#CBD5E1;background:transparent;border:none;"
        )
        title_lay.addWidget(dot)
        title_lay.addWidget(lbl)
        title_lay.addStretch()

        lay.addWidget(title_w)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet(f"color:rgba(59,130,246,0.2);background:rgba(59,130,246,0.15);max-height:1px;border:none;")
        lay.addWidget(sep)
        lay.addWidget(canvas)
        return wrapper

    def _kpi_card(self, label: str, value: str, color: str, sub: str):
        card = QWidget()
        card.setMinimumHeight(110)
        card.setStyleSheet(
            f"background: qlineargradient(x1:0,y1:0,x2:1,y2:1,"
            f"stop:0 rgba(15,23,42,0.95), stop:1 rgba(22,38,70,0.95));"
            f"border-radius:14px;"
            f"border:1px solid rgba(59,130,246,0.25);"
            f"border-top:2px solid {color};"
        )
        lay = QVBoxLayout(card)
        lay.setContentsMargins(14, 14, 14, 12)
        lay.setSpacing(4)

        val_lbl = QLabel(value)
        val_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        val_lbl.setStyleSheet(
            f"font-family:'Arial','KaiTi',sans-serif;font-size:30px;font-weight:bold;"
            f"color:{color};background:transparent;border:none;"
        )
        name_lbl = QLabel(label)
        name_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        name_lbl.setStyleSheet(
            "font-family:'KaiTi','楷体',serif;font-size:13px;font-weight:bold;"
            "color:#94A3B8;background:transparent;border:none;"
        )
        sub_lbl = QLabel(sub)
        sub_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sub_lbl.setStyleSheet(
            f"font-family:'SimSun','宋体',serif;font-size:10px;"
            f"color:{color};opacity:0.7;background:transparent;border:none;"
        )
        lay.addWidget(val_lbl)
        lay.addWidget(name_lbl)
        lay.addWidget(sub_lbl)
        card._val_lbl = val_lbl
        return card, val_lbl

    def _mini_stat_card(self, label: str, value: str, color: str):
        card = QWidget()
        card.setMinimumHeight(80)
        card.setStyleSheet(
            f"background:rgba(15,23,42,0.88);"
            f"border-radius:12px;"
            f"border:1px solid rgba(59,130,246,0.2);"
            f"border-left:2px solid {color};"
        )
        lay = QVBoxLayout(card)
        lay.setContentsMargins(12, 10, 12, 10)
        lay.setSpacing(3)
        val_lbl = QLabel(value)
        val_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        val_lbl.setStyleSheet(
            f"font-family:'Arial',sans-serif;font-size:22px;font-weight:bold;"
            f"color:{color};background:transparent;border:none;"
        )
        name_lbl = QLabel(label)
        name_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        name_lbl.setStyleSheet(
            "font-family:'SimSun','宋体',serif;font-size:11px;"
            "color:#64748B;background:transparent;border:none;"
        )
        lay.addWidget(val_lbl)
        lay.addWidget(name_lbl)
        card._val_lbl = val_lbl
        return card, val_lbl

    # ────────────────── 数据加载 ──────────────────────────────────────
    def _load_data(self):
        cfg = storage.load_config()
        self.metrics_dir = storage.resolve_path(cfg.get("metrics_dir", ""))
        csv_path = os.path.join(self.metrics_dir, "results.csv")

        if os.path.exists(csv_path):
            try:
                import pandas as pd
                self.csv_data = pd.read_csv(csv_path)
                self.csv_data.columns = [c.strip() for c in self.csv_data.columns]
                self._plot_curves()
                self._update_metric_summary()
            except Exception as e:
                self._show_no_data(f"加载 CSV 失败：{e}")
        else:
            self._show_no_data(f"未找到 results.csv\n{csv_path}")

    def _show_no_data(self, msg: str):
        for key, (fig, canvas) in self.curve_figs.items():
            fig.clear()
            ax = fig.add_subplot(111)
            ax.set_facecolor(C["ax_bg"])
            fig.patch.set_facecolor(C["fig_bg"])
            ax.text(0.5, 0.5, msg, ha="center", va="center",
                    transform=ax.transAxes, fontsize=10, color="#475569", wrap=True)
            for sp in ax.spines.values():
                sp.set_color(C["spine"])
            canvas.draw()

    # ────────────────── 绘图 ─────────────────────────────────────────
    def _plot_curves(self):
        df = self.csv_data
        epochs = df.get("epoch", range(len(df)))

        def draw(key, col_map, title, ylabel, pct=False):
            fig, canvas = self.curve_figs[key]
            fig.clear()
            ax = fig.add_subplot(111)
            fig.patch.set_facecolor(C["fig_bg"])
            for col, (lbl, clr) in col_map.items():
                if col in df.columns:
                    y = df[col] * 100 if pct else df[col]
                    ax.plot(epochs, y, label=lbl, color=clr, linewidth=1.8, alpha=0.95)
                    _fill_under(ax, epochs, y, clr)
            ax.set_title(title, fontsize=11, color=C["title"], fontweight="bold", pad=8)
            _style_ax(ax, ylabel=ylabel)
            if pct:
                ax.yaxis.set_major_formatter(mtick.FormatStrFormatter("%.1f"))
            leg = ax.legend(fontsize=8, framealpha=0.15, facecolor="#0f172a",
                            edgecolor=C["spine"], labelcolor=C["text"])
            for line in leg.get_lines():
                line.set_linewidth(2)
            fig.tight_layout(pad=1.4)
            canvas.draw()

        draw("train_loss", {
            "train/box_loss": ("Box Loss", C["blue"]),
            "train/cls_loss": ("Cls Loss", C["purple"]),
            "train/dfl_loss": ("DFL Loss", C["teal"]),
        }, "训练损失曲线", "Loss")

        draw("val_loss", {
            "val/box_loss": ("Val Box Loss", C["rose"]),
            "val/cls_loss": ("Val Cls Loss", C["amber"]),
            "val/dfl_loss": ("Val DFL Loss", C["cyan"]),
        }, "验证损失曲线", "Loss")

        draw("map50", {
            "metrics/mAP50(B)":     ("mAP@0.5",      C["blue"]),
            "metrics/mAP50-95(B)":  ("mAP@0.5:0.95", C["indigo"]),
        }, "mAP 指标曲线", "mAP (%)", pct=True)

        draw("pr_curve", {
            "metrics/precision(B)": ("Precision", C["teal"]),
            "metrics/recall(B)":    ("Recall",    C["rose"]),
        }, "精确率 & 召回率", "(%)", pct=True)

    def _update_metric_summary(self):
        df = self.csv_data
        if df is None or len(df) == 0:
            return

        last = df.iloc[-1]
        if "metrics/mAP50(B)" in df.columns:
            best_row = df.loc[df["metrics/mAP50(B)"].idxmax()]
        else:
            best_row = last

        def pct(v):
            return f"{float(v) * 100:.2f}%"

        mapping = {
            "metrics/mAP50(B)":    ("mAP50",     pct),
            "metrics/mAP50-95(B)": ("mAP5095",   pct),
            "metrics/precision(B)":("precision",  pct),
            "metrics/recall(B)":   ("recall",     pct),
        }
        for col, (key, fmt) in mapping.items():
            if col in df.columns:
                self.big_stats[key].setText(fmt(best_row[col]))

        loss_mapping = {
            "train/box_loss": "train_box",
            "train/cls_loss": "train_cls",
            "train/dfl_loss": "train_dfl",
            "val/box_loss":   "val_box",
        }
        for col, key in loss_mapping.items():
            if col in df.columns:
                self.loss_stats[key].setText(f"{float(last[col]):.4f}")

        # 总览图
        self.best_fig.clear()
        ax = self.best_fig.add_subplot(111)
        self.best_fig.patch.set_facecolor(C["fig_bg"])
        epochs = df.get("epoch", range(len(df)))
        overview_cols = {
            "metrics/mAP50(B)":     ("mAP@0.5",   C["blue"]),
            "metrics/mAP50-95(B)":  ("mAP@0.5:0.95", C["indigo"]),
            "metrics/precision(B)": ("Precision",  C["teal"]),
            "metrics/recall(B)":    ("Recall",     C["rose"]),
        }
        for col, (lbl, clr) in overview_cols.items():
            if col in df.columns:
                y = df[col] * 100
                ax.plot(epochs, y, label=lbl, color=clr, linewidth=2, alpha=0.95)
                _fill_under(ax, epochs, y, clr, alpha=0.08)

        ax.set_title("关键指标收敛总览", fontsize=12, color=C["title"], fontweight="bold", pad=10)
        _style_ax(ax, ylabel="(%)")
        ax.yaxis.set_major_formatter(mtick.FormatStrFormatter("%.1f"))
        leg = ax.legend(fontsize=9, loc="lower right", framealpha=0.2,
                        facecolor="#0f172a", edgecolor=C["spine"], labelcolor=C["text"])
        for line in leg.get_lines():
            line.set_linewidth(2.2)
        self.best_fig.tight_layout(pad=1.5)
        self.best_canvas.draw()
