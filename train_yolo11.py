"""
YOLO11 训练脚本 —— 无人机航拍小目标检测
数据集：VisDrone 2019

使用方法：
    python train_yolo11.py                    # 默认配置训练
    python train_yolo11.py --resume           # 从last.pt续训（补全中断的训练）
    python train_yolo11.py --model yolo11m    # 指定模型大小
    python train_yolo11.py --epochs 200       # 指定轮数
    python train_yolo11.py --imgsz 1280       # 更大分辨率（小目标更佳）
"""

import argparse
import os
import sys
from pathlib import Path

# ─────────────────────────────────────────────────────────────
#  路径设置
# ─────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent
DATA_YAML = BASE_DIR / "dataset_visdrone" / "data.yaml"


# ─────────────────────────────────────────────────────────────
#  自动修正 data.yaml 中的 path 为当前本机绝对路径
# ─────────────────────────────────────────────────────────────
def fix_data_yaml(yaml_path: Path) -> Path:
    """将 data.yaml 的 path 字段更新为本机实际路径，返回修正后的临时 yaml 路径"""
    import yaml

    with open(yaml_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    local_data_dir = str(yaml_path.parent.resolve())
    data["path"] = local_data_dir

    fixed_yaml = yaml_path.parent / "data_local.yaml"
    with open(fixed_yaml, "w", encoding="utf-8") as f:
        yaml.dump(data, f, allow_unicode=True, default_flow_style=False)

    print(f"[INFO] data.yaml path 已更新为: {local_data_dir}")
    print(f"[INFO] 已生成临时配置: {fixed_yaml}")
    return fixed_yaml


# ─────────────────────────────────────────────────────────────
#  VisDrone 小目标检测训练配置说明
# ─────────────────────────────────────────────────────────────
TRAIN_TIPS = """
╔══════════════════════════════════════════════════════════════════╗
║           VisDrone 小目标检测训练注意事项                          ║
╠══════════════════════════════════════════════════════════════════╣
║  1. 图像尺寸建议 ≥ 640，推荐 1280（小目标分辨率更高）              ║
║  2. batch 建议 16-32（显存不足时降低）                            ║
║  3. epochs 建议 200-300（VisDrone 收敛较慢）                     ║
║  4. 推荐开启 mosaic 数据增强（已默认开启）                         ║
║  5. 可使用 --multi_scale 多尺度训练提升小目标性能                  ║
║  6. 训练结果保存在 runs/train/ 目录下                             ║
╚══════════════════════════════════════════════════════════════════╝
"""

# 支持的 YOLO11 模型尺寸
YOLO11_MODELS = {
    "yolo11n": "yolo11n.pt",   # Nano  - 最快，精度较低
    "yolo11s": "yolo11s.pt",   # Small - 速度与精度均衡（推荐）
    "yolo11m": "yolo11m.pt",   # Medium
    "yolo11l": "yolo11l.pt",   # Large
    "yolo11x": "yolo11x.pt",   # Extra Large - 最高精度
}


# ─────────────────────────────────────────────────────────────
#  训练函数
# ─────────────────────────────────────────────────────────────
def train(args):
    from ultralytics import YOLO

    print(TRAIN_TIPS)

    # 确定 data.yaml 路径
    if not DATA_YAML.exists():
        print(f"[ERROR] 未找到数据集配置文件: {DATA_YAML}")
        sys.exit(1)

    # 修正 data.yaml 路径
    data_path = fix_data_yaml(DATA_YAML)

    # 确定模型权重（续训时使用 last.pt）
    if args.resume:
        resume_pt = Path(args.project) / args.name / "weights" / "last.pt"
        if not resume_pt.exists():
            print(f"[ERROR] 续训失败：未找到 {resume_pt}")
            sys.exit(1)
        model_name = str(resume_pt)
        print(f"\n[INFO] 续训模式：从 {model_name} 恢复")
    else:
        model_name = args.model
        if not model_name.endswith(".pt") and not model_name.endswith(".yaml"):
            model_name = YOLO11_MODELS.get(model_name, f"{model_name}.pt")

    print(f"\n[INFO] 模型: {model_name}")
    print(f"[INFO] 数据集: {data_path}")
    print(f"[INFO] 训练轮数: {args.epochs}")
    print(f"[INFO] 图像尺寸: {args.imgsz}")
    print(f"[INFO] batch 大小: {args.batch}")
    print(f"[INFO] 设备: {args.device}")
    print(f"[INFO] 实验名称: {args.name}\n")

    # 加载模型（预训练权重微调）
    model = YOLO(model_name)

    # ─── 开始训练 ───
    train_kw = dict(
        data=str(data_path),
        epochs=args.epochs,
        imgsz=args.imgsz,
        batch=args.batch,
        device=args.device,
        workers=args.workers,
        project=args.project,
        name=args.name,
        exist_ok=args.exist_ok,

        # ── 优化器 ──
        optimizer="SGD",        # SGD 在检测任务上通常优于 Adam
        lr0=args.lr0,           # 初始学习率
        lrf=args.lrf,           # 最终学习率 = lr0 * lrf
        momentum=0.937,
        weight_decay=0.0005,
        warmup_epochs=3.0,
        warmup_momentum=0.8,
        warmup_bias_lr=0.1,

        # ── AMP 混合精度 ──
        amp=True,               # 自动混合精度，加速训练且节省显存

        # ── 数据增强 ──
        mosaic=1.0,             # Mosaic 增强（对小目标非常有效）
        mixup=0.0,              # Mixup（VisDrone 通常不用）
        copy_paste=args.copy_paste,   # 复制粘贴增强（对密集小目标有帮助）
        hsv_h=0.015,
        hsv_s=0.7,
        hsv_v=0.4,
        degrees=0.0,
        translate=0.1,
        scale=0.5,
        shear=0.0,
        perspective=0.0,
        flipud=0.0,
        fliplr=0.5,
        erasing=0.4,
        auto_augment="randaugment",
        close_mosaic=10,        # 最后 10 个 epoch 关闭 mosaic 以稳定收敛

        # ── 损失权重 ──
        box=7.5,
        cls=0.5,
        dfl=1.5,

        # ── 其他 ──
        multi_scale=args.multi_scale,  # 多尺度训练
        patience=args.patience,        # Early stopping
        save_period=args.save_period,  # 每 N 个 epoch 保存一次
        plots=True,             # 保存训练过程图表
        verbose=True,
        seed=args.seed,
        deterministic=True,
        pretrained=True,        # 使用预训练权重
        val=True,
        iou=0.7,
        max_det=300,
        label_smoothing=0.0,
    )
    if args.resume:
        train_kw["resume"] = True
    results = model.train(**train_kw)

    print("\n" + "═" * 60)
    print("  ✅ 训练完成！")
    print(f"  📁 结果保存在: {args.project}/{args.name}/")
    print(f"  🏆 最佳权重: {args.project}/{args.name}/weights/best.pt")
    print(f"  📊 训练曲线: {args.project}/{args.name}/results.png")
    print("═" * 60)

    return results


# ─────────────────────────────────────────────────────────────
#  验证函数
# ─────────────────────────────────────────────────────────────
def validate(args):
    from ultralytics import YOLO

    if not args.weights:
        print("[ERROR] 验证时需指定 --weights 权重路径")
        sys.exit(1)

    data_path = fix_data_yaml(DATA_YAML)
    model = YOLO(args.weights)

    print(f"\n[INFO] 开始验证: {args.weights}")
    metrics = model.val(
        data=str(data_path),
        imgsz=args.imgsz,
        batch=args.batch,
        device=args.device,
        split="val",            # 使用验证集
        plots=True,
        verbose=True,
    )

    print("\n" + "═" * 60)
    print("  📊 验证结果：")
    print(f"  Precision : {metrics.box.mp:.4f}")
    print(f"  Recall    : {metrics.box.mr:.4f}")
    print(f"  mAP@0.5   : {metrics.box.map50:.4f}")
    print(f"  mAP@0.5:95: {metrics.box.map:.4f}")
    print("═" * 60)
    return metrics


# ─────────────────────────────────────────────────────────────
#  预测推理函数
# ─────────────────────────────────────────────────────────────
def predict(args):
    from ultralytics import YOLO

    if not args.weights:
        print("[ERROR] 推理时需指定 --weights 权重路径")
        sys.exit(1)
    if not args.source:
        print("[ERROR] 推理时需指定 --source 图片/视频路径")
        sys.exit(1)

    model = YOLO(args.weights)
    results = model.predict(
        source=args.source,
        imgsz=args.imgsz,
        conf=args.conf,
        iou=0.7,
        device=args.device,
        save=True,
        save_txt=True,
        save_conf=True,
        project=args.project,
        name=f"{args.name}_predict",
        show_labels=True,
        show_conf=True,
        verbose=True,
    )
    print(f"\n✅ 推理完成，结果保存在: {args.project}/{args.name}_predict/")
    return results


# ─────────────────────────────────────────────────────────────
#  命令行参数
# ─────────────────────────────────────────────────────────────
def parse_args():
    parser = argparse.ArgumentParser(
        description="YOLO11 训练脚本 —— VisDrone 无人机小目标检测",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    # 模式选择
    parser.add_argument("--mode", type=str, default="train",
                        choices=["train", "val", "predict"],
                        help="运行模式：train训练 / val验证 / predict推理")

    # 模型
    parser.add_argument("--model", type=str, default="yolo11s",
                        choices=list(YOLO11_MODELS.keys()) + list(YOLO11_MODELS.values()),
                        help="YOLO11 模型尺寸或权重路径")
    parser.add_argument("--weights", type=str, default="",
                        help="val/predict 模式下指定权重路径，如 runs/train/exp/weights/best.pt")

    # 训练超参数
    parser.add_argument("--epochs", type=int, default=300,
                        help="训练轮数")
    parser.add_argument("--imgsz", type=int, default=640,
                        help="训练图像尺寸（小目标建议 1280）")
    parser.add_argument("--batch", type=int, default=16,
                        help="批大小（显存不足时减小）")
    parser.add_argument("--lr0", type=float, default=0.01,
                        help="初始学习率")
    parser.add_argument("--lrf", type=float, default=0.01,
                        help="最终学习率比例（lr_final = lr0 * lrf）")
    parser.add_argument("--patience", type=int, default=100,
                        help="Early stopping 等待轮数（0=关闭）")
    parser.add_argument("--multi_scale", action="store_true",
                        help="开启多尺度训练（±50%范围，对小目标有帮助）")
    parser.add_argument("--copy_paste", type=float, default=0.0,
                        help="Copy-paste 数据增强概率（0=关闭，推荐 0.1）")

    # 设备
    parser.add_argument("--device", type=str, default="",
                        help="训练设备：0/1/2（GPU编号）、0,1（多卡）、cpu")
    parser.add_argument("--workers", type=int, default=4,
                        help="DataLoader 工作进程数")

    # 保存
    parser.add_argument("--project", type=str, default="runs/train",
                        help="实验保存目录")
    parser.add_argument("--name", type=str, default="yolo11_visdrone",
                        help="实验名称")
    parser.add_argument("--exist_ok", action="store_true",
                        help="允许覆盖已有实验目录")
    parser.add_argument("--resume", action="store_true",
                        help="从 last.pt 续训，补全中断的训练结果")
    parser.add_argument("--save_period", type=int, default=-1,
                        help="每 N 个 epoch 额外保存检查点（-1=只保存 best/last）")
    parser.add_argument("--seed", type=int, default=0,
                        help="随机种子，保证可复现性")

    # 推理参数
    parser.add_argument("--source", type=str, default="",
                        help="predict 模式下的输入图片/视频路径")
    parser.add_argument("--conf", type=float, default=0.25,
                        help="predict 模式下的置信度阈值")

    return parser.parse_args()


# ─────────────────────────────────────────────────────────────
#  主函数
# ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    args = parse_args()

    # 检查 ultralytics 是否安装
    try:
        import ultralytics
        print(f"[INFO] Ultralytics 版本: {ultralytics.__version__}")
    except ImportError:
        print("[ERROR] 未安装 ultralytics，请运行: pip install ultralytics")
        sys.exit(1)

    # 检查 PyYAML
    try:
        import yaml
    except ImportError:
        print("[ERROR] 未安装 PyYAML，请运行: pip install pyyaml")
        sys.exit(1)

    if args.mode == "train":
        train(args)
    elif args.mode == "val":
        validate(args)
    elif args.mode == "predict":
        predict(args)
