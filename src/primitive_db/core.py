from typing import Any, Dict, List, Tuple

from .constants import VALID_TYPES


def _get_table_schema(
    metadata: Dict[str, Any],
    table_name: str,
) -> List[Dict[str, Any]]:
    if table_name not in metadata:
        raise ValueError(f'Ошибка: Таблица "{table_name}" не существует.')
    return metadata[table_name]["columns"]


def create_table(
    metadata: Dict[str, Any],
    table_name: str,
    columns: List[Tuple[str, str]],
) -> Dict[str, Any]:
    if table_name in metadata:
        raise ValueError(f'Ошибка: Таблица "{table_name}" уже существует.')

    full_columns: List[Tuple[str, str]] = [("ID", "int")]
    for name, col_type in columns:
        if name.lower() == "id":
            continue
        if col_type not in VALID_TYPES:
            raise ValueError(
                f"Некорректный тип столбца: {col_type}. "
                "Допустимые типы: int, str, bool.",
            )
        full_columns.append((name, col_type))

    metadata[table_name] = {
        "columns": [
            {"name": name, "type": col_type}
            for name, col_type in full_columns
        ],
    }
    return metadata


def drop_table(
    metadata: Dict[str, Any],
    table_name: str,
) -> Dict[str, Any]:
    if table_name not in metadata:
        raise ValueError(f'Ошибка: Таблица "{table_name}" не существует.')

    del metadata[table_name]
    return metadata


def _next_id(table_data: List[Dict[str, Any]]) -> int:
    if not table_data:
        return 1
    max_id = max(int(row.get("ID", 0)) for row in table_data)
    return max_id + 1


def _validate_type(expected: str, value: Any) -> None:
    if expected == "int" and not isinstance(value, int):
        raise ValueError(f"Некорректное значение: {value}. Попробуйте снова.")
    if expected == "str" and not isinstance(value, str):
        raise ValueError(f"Некорректное значение: {value}. Попробуйте снова.")
    if expected == "bool" and not isinstance(value, bool):
        raise ValueError(f"Некорректное значение: {value}. Попробуйте снова.")


def insert_row(
    metadata: Dict[str, Any],
    table_name: str,
    values: List[Any],
    table_data: List[Dict[str, Any]],
) -> Tuple[List[Dict[str, Any]], int]:
    columns = _get_table_schema(metadata, table_name)
    non_id_columns = [c for c in columns if c["name"] != "ID"]

    if len(values) != len(non_id_columns):
        raise ValueError("Некорректное количество значений для вставки.")

    row: Dict[str, Any] = {}
    row_id = _next_id(table_data)
    row["ID"] = row_id

    for col, value in zip(non_id_columns, values):
        _validate_type(col["type"], value)
        row[col["name"]] = value

    table_data.append(row)
    return table_data, row_id


def select_rows(
    metadata: Dict[str, Any],
    table_name: str,
    table_data: List[Dict[str, Any]],
    where_clause: Dict[str, Any] | None,
) -> List[Dict[str, Any]]:
    _get_table_schema(metadata, table_name)

    if not where_clause:
        return list(table_data)

    result: List[Dict[str, Any]] = []
    for row in table_data:
        matches = True
        for col, value in where_clause.items():
            if row.get(col) != value:
                matches = False
                break
        if matches:
            result.append(row)
    return result


def update_rows(
    metadata: Dict[str, Any],
    table_name: str,
    table_data: List[Dict[str, Any]],
    set_clause: Dict[str, Any],
    where_clause: Dict[str, Any],
) -> Tuple[List[Dict[str, Any]], List[int]]:
    columns = _get_table_schema(metadata, table_name)
    column_names = {c["name"] for c in columns}

    for col in set_clause:
        if col not in column_names:
            raise ValueError(f'Ошибка: столбец "{col}" не существует.')

    updated_ids: List[int] = []
    for row in table_data:
        matches = True
        for col, value in where_clause.items():
            if row.get(col) != value:
                matches = False
                break
        if not matches:
            continue

        for col, value in set_clause.items():
            schema_col = next(c for c in columns if c["name"] == col)
            _validate_type(schema_col["type"], value)
            row[col] = value

        updated_ids.append(int(row["ID"]))

    return table_data, updated_ids


def delete_rows(
    metadata: Dict[str, Any],
    table_name: str,
    table_data: List[Dict[str, Any]],
    where_clause: Dict[str, Any],
) -> Tuple[List[Dict[str, Any]], List[int]]:
    _get_table_schema(metadata, table_name)

    remaining: List[Dict[str, Any]] = []
    deleted_ids: List[int] = []

    for row in table_data:
        matches = True
        for col, value in where_clause.items():
            if row.get(col) != value:
                matches = False
                break
        if matches:
            deleted_ids.append(int(row.get("ID", 0)))
        else:
            remaining.append(row)

    return remaining, deleted_ids


def get_table_info(
    metadata: Dict[str, Any],
    table_name: str,
    table_data: List[Dict[str, Any]],
) -> str:
    columns = _get_table_schema(metadata, table_name)
    columns_str = ", ".join(f'{c["name"]}:{c["type"]}' for c in columns)
    count = len(table_data)

    lines = [
        f"Таблица: {table_name}",
        f"Столбцы: {columns_str}",
        f"Количество записей: {count}",
    ]
    return "\n".join(lines)
