"""
Вспомогательные функции для работы с JSON.
"""

import json
import os
from typing import Any, Dict, List

from .constants import DATA_DIR, META_FILE


def _ensure_data_dir() -> None:
    """Гарантирует существование директории для данных таблиц."""
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)


def load_metadata(filepath: str = META_FILE) -> Dict[str, Any]:
    """Загружает метаданные из JSON-файла."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def save_metadata(filepath: str, data: Dict[str, Any]) -> None:
    """Сохраняет метаданные в JSON-файл."""
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_table_data(table_name: str) -> List[Dict[str, Any]]:
    """Загружает записи конкретной таблицы."""
    _ensure_data_dir()
    path = os.path.join(DATA_DIR, f"{table_name}.json")
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def save_table_data(table_name: str, data: List[Dict[str, Any]]) -> None:
    """Сохраняет записи конкретной таблицы в JSON."""
    _ensure_data_dir()
    path = os.path.join(DATA_DIR, f"{table_name}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
