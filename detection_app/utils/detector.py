"""
YOLO 检测器封装，图片/视频/摄像头检测工作线程及结果保存。
@作者：Jay
@定制联系vx：Jay8059
@开发日期：2026年
"""

import os
import csv
import numpy as np
from datetime import datetime
from pathlib import Path

from PyQt6.QtCore import QThread, pyqtSignal, QObject

# VisDrone 类别名称
CLASS_NAMES_CN = {
    0: "行人",
    1: "人群",
    2: "自行车",
    3: "小汽车",
    4: "面包车",
    5: "卡车",
    6: "三轮车",
    7: "带篷三轮车",
    8: "公交车",
    9: "摩托车"
}
CLASS_NAMES_EN = {
    0: "pedestrian", 1: "people", 2: "bicycle", 3: "car",
    4: "van", 5: "truck", 6: "tricycle", 7: "awning-tricycle",
    8: "bus", 9: "motor"
}
# 每个类别对应颜色 (BGR for cv2)
CLASS_COLORS_BGR = [
    (255, 87, 51), (255, 195, 0), (0, 200, 83), (33, 150, 243),
    (156, 39, 176), (255, 152, 0), (0, 188, 212), (233, 30, 99),
    (76, 175, 80), (103, 58, 183)
]

_model_instance = None
_model_path_loaded = ""


def get_model(model_path: str):
    """单例模式获取模型"""
    global _model_instance, _model_path_loaded
    if _model_instance is None or _model_path_loaded != model_path:
        from ultralytics import YOLO
        _model_instance = YOLO(model_path)
        _model_path_loaded = model_path
    return _model_instance


def parse_results(results, conf_threshold: float = 0.0) -> dict:
    """解析 YOLO 结果为结构化数据"""
    detections = []
    class_counts = {}
    conf_list = []

    for r in results:
        if r.boxes is None:
            continue
        boxes = r.boxes
        for i in range(len(boxes)):
            conf = float(boxes.conf[i])
            if conf < conf_threshold:
                continue
            cls_id = int(boxes.cls[i])
            x1, y1, x2, y2 = [float(v) for v in boxes.xyxy[i]]
            w = x2 - x1
            h = y2 - y1
            area = w * h
            cn = CLASS_NAMES_CN.get(cls_id, f"类别{cls_id}")
            detections.append({
                "class_id": cls_id,
                "class_name": cn,
                "class_en": CLASS_NAMES_EN.get(cls_id, f"cls{cls_id}"),
                "confidence": round(conf, 4),
                "x1": round(x1, 1), "y1": round(y1, 1),
                "x2": round(x2, 1), "y2": round(y2, 1),
                "width": round(w, 1), "height": round(h, 1),
                "area": round(area, 1)
            })
            class_counts[cn] = class_counts.get(cn, 0) + 1
            conf_list.append(conf)

    avg_conf = round(float(np.mean(conf_list)), 4) if conf_list else 0.0
    max_conf = round(float(np.max(conf_list)), 4) if conf_list else 0.0
    min_conf = round(float(np.min(conf_list)), 4) if conf_list else 0.0

    return {
        "detections": detections,
        "total": len(detections),
        "class_counts": class_counts,
        "avg_conf": avg_conf,
        "max_conf": max_conf,
        "min_conf": min_conf
    }


def save_results_csv(detections: list, save_path: str):
    """保存检测结果为 CSV"""
    fieldnames = ["序号", "类别", "置信度", "X1", "Y1", "X2", "Y2", "宽度", "高度", "面积"]
    with open(save_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for i, d in enumerate(detections, 1):
            writer.writerow({
                "序号": i,
                "类别": d["class_name"],
                "置信度": f"{d['confidence']:.4f}",
                "X1": d["x1"], "Y1": d["y1"],
                "X2": d["x2"], "Y2": d["y2"],
                "宽度": d["width"], "高度": d["height"],
                "面积": d["area"]
            })


# ============================================================
#  图片检测线程
# ============================================================
class ImageDetectWorker(QThread):
    finished = pyqtSignal(dict)   # {'annotated_img': ndarray, 'parsed': dict}
    error = pyqtSignal(str)

    def __init__(self, model_path: str, image_path: str, conf: float, iou: float):
        super().__init__()
        self.model_path = model_path
        self.image_path = image_path
        self.conf = conf
        self.iou = iou

    def run(self):
        try:
            model = get_model(self.model_path)
            results = model(self.image_path, conf=self.conf, iou=self.iou, verbose=False)
            annotated = results[0].plot()   # BGR ndarray
            parsed = parse_results(results, conf_threshold=0.0)
            self.finished.emit({"annotated_img": annotated, "parsed": parsed})
        except Exception as e:
            self.error.emit(str(e))


# ============================================================
#  视频检测线程
# ============================================================
class VideoDetectWorker(QThread):
    frame_ready = pyqtSignal(object, dict)   # (frame_ndarray_BGR, parsed)
    progress = pyqtSignal(int, int)          # (current_frame, total_frames)
    finished = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, model_path: str, video_path: str, conf: float, iou: float, skip: int = 1):
        super().__init__()
        self.model_path = model_path
        self.video_path = video_path
        self.conf = conf
        self.iou = iou
        self.skip = skip        # 每 skip 帧检测一次
        self._running = True

    def stop(self):
        self._running = False

    def run(self):
        try:
            import cv2
            cap = cv2.VideoCapture(self.video_path)
            total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            model = get_model(self.model_path)
            frame_idx = 0
            while self._running:
                ret, frame = cap.read()
                if not ret:
                    break
                frame_idx += 1
                self.progress.emit(frame_idx, total)
                if frame_idx % self.skip == 0:
                    results = model(frame, conf=self.conf, iou=self.iou, verbose=False)
                    annotated = results[0].plot()
                    parsed = parse_results(results)
                    self.frame_ready.emit(annotated, parsed)
                else:
                    self.frame_ready.emit(frame, {})
            cap.release()
            self.finished.emit()
        except Exception as e:
            self.error.emit(str(e))


# ============================================================
#  摄像头检测线程
# ============================================================
class CameraDetectWorker(QThread):
    frame_ready = pyqtSignal(object, dict)
    error = pyqtSignal(str)

    def __init__(self, model_path: str, camera_index: int, conf: float, iou: float,
                 detect_every: int = 3):
        super().__init__()
        self.model_path = model_path
        self.camera_index = camera_index
        self.conf = conf
        self.iou = iou
        self.detect_every = detect_every
        self._running = True
        self._detect_active = True

    def stop(self):
        self._running = False

    def set_detect(self, active: bool):
        self._detect_active = active

    def run(self):
        try:
            import cv2
            cap = cv2.VideoCapture(self.camera_index)
            if not cap.isOpened():
                self.error.emit(f"无法打开摄像头 {self.camera_index}")
                return
            model = get_model(self.model_path)
            frame_idx = 0
            last_annotated = None
            last_parsed = {}
            while self._running:
                ret, frame = cap.read()
                if not ret:
                    break
                frame_idx += 1
                if self._detect_active and frame_idx % self.detect_every == 0:
                    results = model(frame, conf=self.conf, iou=self.iou, verbose=False)
                    last_annotated = results[0].plot()
                    last_parsed = parse_results(results)
                    self.frame_ready.emit(last_annotated, last_parsed)
                elif last_annotated is not None:
                    self.frame_ready.emit(last_annotated, last_parsed)
                else:
                    self.frame_ready.emit(frame, {})
            cap.release()
        except Exception as e:
            self.error.emit(str(e))


# ============================================================
#  模型加载线程
# ============================================================
class ModelLoadWorker(QThread):
    finished = pyqtSignal(bool, str)   # (success, message)

    def __init__(self, model_path: str):
        super().__init__()
        self.model_path = model_path

    def run(self):
        try:
            if not os.path.exists(self.model_path):
                self.finished.emit(False, f"文件不存在：{self.model_path}")
                return
            global _model_instance, _model_path_loaded
            from ultralytics import YOLO
            _model_instance = YOLO(self.model_path)
            _model_path_loaded = self.model_path
            self.finished.emit(True, "模型加载成功")
        except Exception as e:
            self.finished.emit(False, f"加载失败：{e}")
