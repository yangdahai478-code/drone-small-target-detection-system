"""
基于 results.csv 生成训练指标可视化图表。
"""

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

plt.rcParams["font.sans-serif"] = ["SimSun", "宋体", "Microsoft YaHei", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False

COLORS = {
    "primary": "#4A6CF7",
    "secondary": "#7B4FB8",
    "success": "#06D6A0",
    "danger": "#FF6B6B",
    "warn": "#FFB347",
    "info": "#45B7D1",
    "bg": "#FAFBFF",
    "grid": "#EEF0FF",
    "text": "#5A6A8A",
    "title": "#3A3FC4",
}


def style_ax(ax, xlabel="Epoch", ylabel=""):
    ax.set_facecolor(COLORS["bg"])
    ax.set_xlabel(xlabel, fontsize=10, color=COLORS["text"])
    ax.set_ylabel(ylabel, fontsize=10, color=COLORS["text"])
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color(COLORS["grid"])
    ax.spines["bottom"].set_color(COLORS["grid"])
    ax.tick_params(colors=COLORS["text"], labelsize=9)
    ax.grid(True, linestyle="--", alpha=0.4, color=COLORS["grid"])


def plot_train_loss(df, save_dir):
    fig, ax = plt.subplots(figsize=(8, 5), facecolor=COLORS["bg"])
    epochs = df["epoch"]
    if "train/box_loss" in df.columns:
        ax.plot(epochs, df["train/box_loss"], label="Box Loss", color=COLORS["primary"], lw=1.8)
    if "train/cls_loss" in df.columns:
        ax.plot(epochs, df["train/cls_loss"], label="Cls Loss", color=COLORS["secondary"], lw=1.8)
    if "train/dfl_loss" in df.columns:
        ax.plot(epochs, df["train/dfl_loss"], label="DFL Loss", color=COLORS["success"], lw=1.8)
    ax.set_title("训练损失曲线", fontsize=14, color=COLORS["title"], fontweight="bold")
    style_ax(ax, ylabel="Loss")
    ax.legend(fontsize=10)
    fig.tight_layout()
    fig.savefig(save_dir / "train_loss.png", dpi=120, bbox_inches="tight")
    plt.close(fig)


def plot_val_loss(df, save_dir):
    fig, ax = plt.subplots(figsize=(8, 5), facecolor=COLORS["bg"])
    epochs = df["epoch"]
    if "val/box_loss" in df.columns:
        ax.plot(epochs, df["val/box_loss"], label="Val Box Loss", color=COLORS["danger"], lw=1.8)
    if "val/cls_loss" in df.columns:
        ax.plot(epochs, df["val/cls_loss"], label="Val Cls Loss", color=COLORS["warn"], lw=1.8)
    if "val/dfl_loss" in df.columns:
        ax.plot(epochs, df["val/dfl_loss"], label="Val DFL Loss", color=COLORS["info"], lw=1.8)
    ax.set_title("验证损失曲线", fontsize=14, color=COLORS["title"], fontweight="bold")
    style_ax(ax, ylabel="Loss")
    ax.legend(fontsize=10)
    fig.tight_layout()
    fig.savefig(save_dir / "val_loss.png", dpi=120, bbox_inches="tight")
    plt.close(fig)


def plot_map_curves(df, save_dir):
    fig, ax = plt.subplots(figsize=(8, 5), facecolor=COLORS["bg"])
    epochs = df["epoch"]
    if "metrics/mAP50(B)" in df.columns:
        ax.plot(epochs, df["metrics/mAP50(B)"] * 100, label="mAP@0.5", color=COLORS["primary"], lw=2)
    if "metrics/mAP50-95(B)" in df.columns:
        ax.plot(epochs, df["metrics/mAP50-95(B)"] * 100, label="mAP@0.5:0.95",
                color=COLORS["secondary"], lw=2, linestyle="--")
    ax.set_title("mAP 指标曲线", fontsize=14, color=COLORS["title"], fontweight="bold")
    style_ax(ax, ylabel="mAP (%)")
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{x:.1f}"))
    ax.legend(fontsize=10)
    fig.tight_layout()
    fig.savefig(save_dir / "map_curves.png", dpi=120, bbox_inches="tight")
    plt.close(fig)


def plot_precision_recall(df, save_dir):
    fig, ax = plt.subplots(figsize=(8, 5), facecolor=COLORS["bg"])
    epochs = df["epoch"]
    if "metrics/precision(B)" in df.columns:
        ax.plot(epochs, df["metrics/precision(B)"] * 100, label="Precision",
                color=COLORS["success"], lw=2)
    if "metrics/recall(B)" in df.columns:
        ax.plot(epochs, df["metrics/recall(B)"] * 100, label="Recall",
                color=COLORS["danger"], lw=2)
    ax.set_title("精确率 & 召回率曲线", fontsize=14, color=COLORS["title"], fontweight="bold")
    style_ax(ax, ylabel="(%)")
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{x:.1f}"))
    ax.legend(fontsize=10)
    fig.tight_layout()
    fig.savefig(save_dir / "precision_recall.png", dpi=120, bbox_inches="tight")
    plt.close(fig)


def plot_learning_rate(df, save_dir):
    fig, ax = plt.subplots(figsize=(8, 5), facecolor=COLORS["bg"])
    epochs = df["epoch"]
    for i, col in enumerate(["lr/pg0", "lr/pg1", "lr/pg2"]):
        if col in df.columns:
            ax.plot(epochs, df[col], label=col.replace("lr/", "LR "), lw=1.5)
    ax.set_title("学习率曲线", fontsize=14, color=COLORS["title"], fontweight="bold")
    style_ax(ax, ylabel="Learning Rate")
    ax.legend(fontsize=10)
    fig.tight_layout()
    fig.savefig(save_dir / "learning_rate.png", dpi=120, bbox_inches="tight")
    plt.close(fig)


def plot_combined_metrics(df, save_dir):
    fig, ax = plt.subplots(figsize=(10, 6), facecolor=COLORS["bg"])
    epochs = df["epoch"]
    cols = [
        ("metrics/mAP50(B)", "mAP@0.5", COLORS["primary"]),
        ("metrics/mAP50-95(B)", "mAP@0.5:0.95", COLORS["secondary"]),
        ("metrics/precision(B)", "Precision", COLORS["success"]),
        ("metrics/recall(B)", "Recall", COLORS["danger"]),
    ]
    for col, lbl, clr in cols:
        if col in df.columns:
            ax.plot(epochs, df[col] * 100, label=lbl, color=clr, lw=1.8)
    ax.set_title("关键指标收敛总览", fontsize=14, color=COLORS["title"], fontweight="bold")
    style_ax(ax, ylabel="(%)")
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{x:.1f}"))
    ax.legend(fontsize=10, loc="lower right")
    fig.tight_layout()
    fig.savefig(save_dir / "combined_metrics.png", dpi=120, bbox_inches="tight")
    plt.close(fig)


def plot_loss_comparison(df, save_dir):
    fig, axes = plt.subplots(2, 1, figsize=(10, 8), facecolor=COLORS["bg"])
    epochs = df["epoch"]

    ax1 = axes[0]
    ax1.set_facecolor(COLORS["bg"])
    if "train/box_loss" in df.columns:
        ax1.plot(epochs, df["train/box_loss"], label="Train Box", color=COLORS["primary"], lw=1.5)
    if "train/cls_loss" in df.columns:
        ax1.plot(epochs, df["train/cls_loss"], label="Train Cls", color=COLORS["secondary"], lw=1.5)
    if "train/dfl_loss" in df.columns:
        ax1.plot(epochs, df["train/dfl_loss"], label="Train DFL", color=COLORS["success"], lw=1.5)
    ax1.set_title("训练损失", fontsize=12, color=COLORS["title"], fontweight="bold")
    style_ax(ax1, ylabel="Loss")
    ax1.legend(fontsize=9)

    ax2 = axes[1]
    ax2.set_facecolor(COLORS["bg"])
    if "val/box_loss" in df.columns:
        ax2.plot(epochs, df["val/box_loss"], label="Val Box", color=COLORS["danger"], lw=1.5)
    if "val/cls_loss" in df.columns:
        ax2.plot(epochs, df["val/cls_loss"], label="Val Cls", color=COLORS["warn"], lw=1.5)
    if "val/dfl_loss" in df.columns:
        ax2.plot(epochs, df["val/dfl_loss"], label="Val DFL", color=COLORS["info"], lw=1.5)
    ax2.set_title("验证损失", fontsize=12, color=COLORS["title"], fontweight="bold")
    style_ax(ax2, ylabel="Loss")
    ax2.legend(fontsize=9)

    fig.suptitle("损失曲线对比", fontsize=14, fontweight="bold", color=COLORS["title"], y=1.02)
    fig.tight_layout()
    fig.savefig(save_dir / "loss_comparison.png", dpi=120, bbox_inches="tight")
    plt.close(fig)


def plot_training_time(df, save_dir):
    fig, ax = plt.subplots(figsize=(8, 5), facecolor=COLORS["bg"])
    epochs = df["epoch"]
    if "time" in df.columns:
        ax.fill_between(epochs, df["time"], alpha=0.3, color=COLORS["primary"])
        ax.plot(epochs, df["time"], color=COLORS["primary"], lw=2, label="累计训练时间 (s)")
    ax.set_title("训练时间累计", fontsize=14, color=COLORS["title"], fontweight="bold")
    style_ax(ax, ylabel="Time (s)")
    ax.legend(fontsize=10)
    fig.tight_layout()
    fig.savefig(save_dir / "training_time.png", dpi=120, bbox_inches="tight")
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", type=str,
                        default="runs/detect/runs/train/yolo11_visdrone/results.csv",
                        help="results.csv 路径")
    parser.add_argument("--out", type=str, default=None,
                        help="输出目录，默认与 csv 同目录")
    args = parser.parse_args()

    csv_path = Path(args.csv)
    if not csv_path.exists():
        print(f"错误：未找到 {csv_path}")
        return

    save_dir = Path(args.out) if args.out else csv_path.parent
    save_dir.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(csv_path)
    df.columns = [c.strip() for c in df.columns]

    plot_train_loss(df, save_dir)
    plot_val_loss(df, save_dir)
    plot_map_curves(df, save_dir)
    plot_precision_recall(df, save_dir)
    plot_learning_rate(df, save_dir)
    plot_combined_metrics(df, save_dir)
    plot_loss_comparison(df, save_dir)
    plot_training_time(df, save_dir)

    print(f"已生成 8 张图表至：{save_dir}")


if __name__ == "__main__":
    main()
