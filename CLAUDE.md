# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目简介
基于 YOLOv11 的无人机航拍小目标检测系统，使用 Ultralytics YOLO11 框架在 VisDrone 2019 数据集上训练，配套 PyQt6 桌面应用支持图片、视频、摄像头实时检测。

## 常用命令

### 环境配置
```bash
# 安装基础依赖
pip install ultralytics torch opencv-python pyyaml numpy pandas matplotlib

# 安装桌面应用依赖
pip install PyQt6 Pillow
```

### 模型训练
```bash
# 默认配置训练 (yolo11s, 300 epochs, imgsz 640)
python train_yolo11.py

# 指定模型大小训练
python train_yolo11.py --model yolo11n
python train_yolo11.py --model yolo11m

# 指定训练轮数和输入尺寸（小目标推荐 1280）
python train_yolo11.py --epochs 200 --imgsz 1280

# 开启多尺度训练提升小目标性能
python train_yolo11.py --multi_scale

# 验证模型
python train_yolo11.py --mode val --weights runs/train/yolo11_visdrone/weights/best.pt

# 推理预测
python train_yolo11.py --mode predict --weights runs/train/yolo11_visdrone/weights/best.pt --source path/to/image.jpg
```

### 生成训练指标图表
```bash
python generate_metrics_charts.py --csv runs/train/yolo11_visdrone/results.csv
```

### 启动桌面应用
```bash
cd detection_app
python main.py
```

## 代码结构

### 根目录
- `train_yolo11.py` - YOLO11 训练主脚本，支持 train/val/predict 三种模式
- `generate_metrics_charts.py` - 训练指标可视化图表生成工具
- `yolo11s.pt`, `yolo26n.pt` - 预训练权重文件

### `dataset_visdrone/` - 数据集
- `data.yaml` - YOLO 数据集配置（10 个类别）
- `data_local.yaml` - 自动生成的本机绝对路径配置
- `VisDrone2019-DET-*/images/` - 图像目录
- `VisDrone2019-DET-*/labels/` - YOLO 格式标注

### `detection_app/` - PyQt6 桌面应用
- `main.py` - 应用入口，启动登录窗口
- `login_window.py` - 登录窗口
- `main_window.py` - 主窗口
- `config.json` - 应用配置（模型路径、检测参数等）
- `requirements.txt` - 依赖列表
- `pages/` - 各功能页面模块
  - `image_page.py` - 图片识别
  - `video_page.py` - 视频识别
  - `camera_page.py` - 摄像头实时识别
  - `history_page.py` - 检测历史
  - `model_page.py` - 模型管理
  - `metrics_page.py` - 训练指标展示
- `utils/` - 工具模块
  - `detector.py` - 检测逻辑（ImageDetectWorker, VideoDetectWorker, CameraDetectWorker）
  - `storage.py` - 配置与存储
  - `styles.py` - 界面样式
- `data/` - 数据存储
  - `users.json` - 用户信息
  - `history.json` - 检测历史记录

### `runs/` - 训练输出
- `runs/train/<exp-name>/` - 训练实验输出
  - `args.yaml` - 训练参数
  - `results.csv` - 训练指标数据
  - `results.png` - 训练曲线
  - `weights/best.pt` - 最佳权重
  - `weights/last.pt` - 最后一轮权重
  - 各种可视化图表

## 类别信息
VisDrone 数据集包含 10 个目标类别：
0: pedestrian (行人), 1: people (人群), 2: bicycle (自行车), 3: car (小汽车), 4: van (面包车),
5: truck (卡车), 6: tricycle (三轮车), 7: awning-tricycle (带篷三轮车), 8: bus (公交车), 9: motor (摩托车)

## 默认配置
- 默认账号：admin / admin123 (桌面应用登录)
- 默认检测参数：conf_threshold=0.25, iou_threshold=0.70, max_det=300
- 默认训练参数：model=yolo11s, epochs=300, imgsz=640, batch=16, lr0=0.01
