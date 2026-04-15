"""
数据存储与配置管理，用户信息、检测历史、模型路径等。
@作者：Jay
@定制联系vx：Jay8059
@开发日期：2026年
"""

import json
import os
import uuid
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List

# 数据目录
BASE_DIR = Path(__file__).parent.parent
PROJECT_ROOT = BASE_DIR.parent
DATA_DIR = BASE_DIR / "data"
CONFIG_FILE = BASE_DIR / "config.json"
USERS_FILE = DATA_DIR / "users.json"
HISTORY_FILE = DATA_DIR / "history.json"

# 默认路径（相对项目根目录）
DEFAULT_MODEL_PATH = "runs/detect/runs/train/yolo11_visdrone/weights/best.pt"
DEFAULT_METRICS_DIR = "runs/detect/runs/train/yolo11_visdrone"


def resolve_path(path: str) -> str:
    if not path:
        return path
    p = Path(path)
    if not p.is_absolute():
        return str(PROJECT_ROOT / path)
    return path


def to_relative_path(path: str) -> str:
    if not path:
        return path
    p = Path(path)
    if not p.is_absolute():
        return path
    try:
        rel = p.resolve().relative_to(Path(PROJECT_ROOT).resolve())
        return str(rel).replace("\\", "/")
    except ValueError:
        return path

DEFAULT_CONFIG = {
    "model_path": DEFAULT_MODEL_PATH,
    "metrics_dir": DEFAULT_METRICS_DIR,
    "conf_threshold": 0.25,
    "iou_threshold": 0.70,
    "max_det": 300,
    "last_user": ""
}


def _hash_password(pwd: str) -> str:
    return hashlib.sha256(pwd.encode("utf-8")).hexdigest()


def ensure_dirs():
    DATA_DIR.mkdir(parents=True, exist_ok=True)


# ============ Config ============

def load_config() -> dict:
    ensure_dirs()
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            cfg = json.load(f)
        # 补全缺失键
        for k, v in DEFAULT_CONFIG.items():
            if k not in cfg:
                cfg[k] = v
        return cfg
    else:
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG.copy()


def save_config(cfg: dict):
    ensure_dirs()
    out = dict(cfg)
    if "model_path" in out and out["model_path"]:
        out["model_path"] = to_relative_path(out["model_path"])
    if "metrics_dir" in out and out["metrics_dir"]:
        out["metrics_dir"] = to_relative_path(out["metrics_dir"])
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)


# ============ Users ============

def _load_users() -> dict:
    ensure_dirs()
    if USERS_FILE.exists():
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    default = {"users": [
        {
            "id": str(uuid.uuid4()),
            "username": "admin",
            "password": _hash_password("admin123"),
            "created_at": datetime.now().isoformat(),
            "role": "管理员"
        }
    ]}
    _save_users(default)
    return default


def _save_users(data: dict):
    ensure_dirs()
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def verify_user(username: str, password: str) -> Optional[Dict]:
    """验证用户，成功返回用户信息，失败返回 None"""
    data = _load_users()
    pwd_hash = _hash_password(password)
    for u in data["users"]:
        if u["username"] == username and u["password"] == pwd_hash:
            return u
    return None


def register_user(username: str, password: str) -> tuple[bool, str]:
    """注册用户。返回 (success, message)"""
    if not username.strip():
        return False, "用户名不能为空"
    if len(password) < 6:
        return False, "密码长度不能少于6位"
    data = _load_users()
    for u in data["users"]:
        if u["username"] == username:
            return False, "用户名已存在"
    data["users"].append({
        "id": str(uuid.uuid4()),
        "username": username,
        "password": _hash_password(password),
        "created_at": datetime.now().isoformat(),
        "role": "普通用户"
    })
    _save_users(data)
    return True, "注册成功"


# ============ History ============

def _load_history_data() -> dict:
    ensure_dirs()
    if HISTORY_FILE.exists():
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"records": []}


def _save_history_data(data: dict):
    ensure_dirs()
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def add_history_record(
    username: str,
    detect_type: str,
    source: str,
    model_path: str,
    total_detections: int,
    class_counts: dict,
    result_image_path: str = "",
    result_csv_path: str = "",
    conf_threshold: float = 0.25,
    notes: str = ""
) -> str:
    """添加一条检测历史记录，返回记录ID"""
    data = _load_history_data()
    record_id = str(uuid.uuid4())[:8].upper()
    record = {
        "id": record_id,
        "timestamp": datetime.now().isoformat(),
        "username": username,
        "type": detect_type,
        "source": to_relative_path(source),
        "model": os.path.basename(model_path),
        "model_path": to_relative_path(model_path),
        "total_detections": total_detections,
        "class_counts": class_counts,
        "result_image_path": to_relative_path(result_image_path),
        "result_csv_path": to_relative_path(result_csv_path),
        "conf_threshold": conf_threshold,
        "notes": notes
    }
    data["records"].insert(0, record)
    _save_history_data(data)
    return record_id


def get_history(username: str = "", limit: int = 0) -> list:
    """获取历史记录，可按用户名过滤"""
    data = _load_history_data()
    records = data["records"]
    if username:
        records = [r for r in records if r.get("username") == username]
    if limit > 0:
        records = records[:limit]
    return records


def export_history_csv(username: str = "", save_path: str = "") -> str:
    """导出历史记录为 CSV，返回保存路径"""
    import csv
    records = get_history(username)
    if not save_path:
        save_path = str(DATA_DIR / f"history_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
    fieldnames = ["id", "timestamp", "username", "type", "source",
                  "model", "total_detections", "class_counts", "conf_threshold", "notes"]
    with open(save_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for r in records:
            row = dict(r)
            row["class_counts"] = str(r.get("class_counts", {}))
            writer.writerow(row)
    return save_path
