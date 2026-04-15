# 基于 YOLOv11 的无人机小目标检测系统

面向无人机航拍场景的小目标检测：基于 **Ultralytics YOLO11**，在 **VisDrone 2019-DET** 上训练与验证，并提供 **PyQt6 桌面应用**（图片 / 视频 / 摄像头检测、模型与指标管理）。

## 功能概览

- **训练与推理**：`train_yolo11.py` 支持训练、验证、单图/视频预测（自动生成本机 `data_local.yaml`）。
- **指标可视化**：`generate_metrics_charts.py` 根据 `results.csv` 导出损失、mAP、学习率等图表。
- **桌面检测系统**：`detection_app` 提供登录、多页面检测与历史记录（依赖见 `detection_app/requirements.txt`）。

## 环境要求

- Python **3.10+**（建议 64 位）
- 训练 / 命令行推理：`pip install ultralytics pyyaml`
- 桌面应用：`pip install -r detection_app/requirements.txt`

## 快速开始

```bash
# 1. 准备 VisDrone 数据（见 dataset_visdrone/data.yaml 与目录约定）

# 2. 训练（项目根目录）
python train_yolo11.py

# 3. （可选）指标图
python generate_metrics_charts.py

# 4. 启动桌面应用
cd detection_app
python main.py
```

默认训练输出一般为 **`runs/train/yolo11_visdrone/weights/best.pt`**。若应用默认模型路径与本地不一致，请在 **「模型管理」** 中重新选择权重，或修改 `detection_app/config.json`。

首次登录桌面应用可使用用户名 **`admin`**、密码 **`admin123`**（亦可注册新用户）。

## 仓库结构（节选）

| 路径 | 说明 |
|------|------|
| `train_yolo11.py` | YOLO11 训练 / 验证 / 预测入口 |
| `generate_metrics_charts.py` | 从 `results.csv` 生成指标 PNG |
| `dataset_visdrone/` | VisDrone 配置与数据目录 |
| `detection_app/` | PyQt6 检测客户端 |
| `运行指南.md` | 环境与排错（最短路径） |
| `项目概述.md` | 数据集、训练细节与类别说明 |

## 文档

- 分步说明与常见问题：**[运行指南.md](运行指南.md)**
- 数据集与训练细节：**[项目概述.md](项目概述.md)**

## 许可证

若使用 **VisDrone** 数据与 **Ultralytics YOLO** 权重，请同时遵守各自官方许可与引用要求。
