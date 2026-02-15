"""
Основная бизнес-логика базы данных: CRUD-операции и управление таблицами.
"""

from typing import Any, Dict, List, Tuple

from .constants import VALID_TYPES


def create_table(
    metadata: Dict[str, Any],
    table_name: str,
    columns: List[Tuple[str, str]]
) -> Dict[str, Any]:
    """Создает новую таблицу в метаданных с автоматическим ID."""
    if table_name in metadata:
        print(f'Ошибка: Таблица "{table_name}" уже существует.')
        return metadata

    # ID всегда идет первым и управляется системой
    full_columns = [{"name": "ID", "type": "int"}]
    for name, col_type in columns:
        if name.upper() == "ID":
            continue
        if col_type not in VALID_TYPES:
            raise ValueError(f"Некорректный тип: {col_type}.")
        full_columns.append({"name": name, "type": col_type})

    metadata[table_name] = {"columns": full_columns}
    return metadata


def drop_table(metadata: Dict[str, Any], table_name: str) -> Dict[str, Any]:
    """Удаляет таблицу из метаданных."""
    if table_name not in metadata:
        raise KeyError(table_name)
    del metadata[table_name]
    return metadata


def insert_row(
    metadata: Dict[str, Any],
    table_name: str,
    values: List[Any],
    table_data: List[Dict[str, Any]]
) -> Tuple[List[Dict[str, Any]], int]:
    """Добавляет новую запись с валидацией типов."""
    schema = metadata[table_name]["columns"]
    non_id_cols = [c for c in schema if c["name"] != "ID"]

    if len(values) != len(non_id_cols):
        raise ValueError("Некорректное количество значений.")

    new_id = max([r["ID"] for r in table_data], default=0) + 1
    new_row = {"ID": new_id}

    for col, val in zip(non_id_cols, values):
        # Проверка типов данных
        if col["type"] == "int" and not isinstance(val, int):
            raise ValueError(f"Некорректное значение: {val}. Ожидался int.")
        if col["type"] == "bool" and not isinstance(val, bool):
            raise ValueError(f"Некорректное значение: {val}. Ожидался bool.")
        new_row[col["name"]] = val

    table_data.append(new_row)
    return table_data, new_id


def select_rows(
    table_data: List[Dict[str, Any]],
    where_clause: Dict[str, Any] = None
) -> List[Dict[str, Any]]:
    """Фильтрует записи по условию WHERE."""
    if not where_clause:
        return table_data

    return [
        row for row in table_data
        if all(row.get(k) == v for k, v in where_clause.items())
    ]


def update_rows(
    metadata: Dict[str, Any],
    table_name: str,
    table_data: List[Dict[str, Any]],
    set_clause: Dict[str, Any],
    where_clause: Dict[str, Any]
) -> Tuple[List[Dict[str, Any]], List[int]]:
    """Обновляет значения в строках, подходящих под условие."""
    schema = metadata[table_name]["columns"]
    updated_ids = []

    for row in table_data:
        # Проверяем условие WHERE
        if all(row.get(k) == v for k, v in where_clause.items()):
            for col_name, new_val in set_clause.items():
                # Валидация типа для обновляемого поля
                col_info = next(c for c in schema if c["name"] == col_name)
                if col_info["type"] == "int" and not isinstance(new_val, int):
                    raise ValueError(f"Ожидался int для {col_name}")
                row[col_name] = new_val
            updated_ids.append(row["ID"])

    return table_data, updated_ids


def delete_rows(
    metadata: Dict[str, Any],
    table_name: str,
    table_data: List[Dict[str, Any]],
    where_clause: Dict[str, Any]
) -> Tuple[List[Dict[str, Any]], List[int]]:
    """Удаляет строки, подходящие под условие."""
    if table_name not in metadata:
        raise KeyError(table_name)

    new_data = []
    deleted_ids = []

    for row in table_data:
        if all(row.get(k) == v for k, v in where_clause.items()):
            deleted_ids.append(row["ID"])
        else:
            new_data.append(row)

    return new_data, deleted_ids


def get_table_info(
    metadata: Dict[str, Any],
    table_name: str,
    table_data: List[Dict[str, Any]]
) -> str:
    """Формирует строковую информацию о таблице."""
    if table_name not in metadata:
        raise KeyError(table_name)

    schema = metadata[table_name]["columns"]
    cols_str = ", ".join(f"{c['name']}:{c['type']}" for c in schema)
    return (
        f"Таблица: {table_name}\n"
        f"Столбцы: {cols_str}\n"
        f"Количество записей: {len(table_data)}"
    )
