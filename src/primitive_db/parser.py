from __future__ import annotations

from typing import Any, Dict, List


def parse_columns(tokens: List[str]) -> List[tuple[str, str]]:
    columns: List[tuple[str, str]] = []
    for token in tokens:
        if ":" not in token:
            raise ValueError(f"Некорректное значение: {token}. Попробуйте снова.")
        name, col_type = token.split(":", 1)
        name = name.strip()
        col_type = col_type.strip()
        if not name or not col_type:
            raise ValueError(f"Некорректное значение: {token}. Попробуйте снова.")
        columns.append((name, col_type))
    return columns


def _convert_literal(raw: str) -> Any:
    raw = raw.strip()
    if raw.startswith('"') and raw.endswith('"') and len(raw) >= 2:
        return raw[1:-1]

    lower = raw.lower()
    if lower == "true":
        return True
    if lower == "false":
        return False

    if raw.isdigit():
        return int(raw)

    raise ValueError(f"Некорректное значение: {raw}. Попробуйте снова.")


def parse_values_part(values_part: str) -> List[Any]:
    text = values_part.strip()
    if text.startswith("values"):
        _, _, text = text.partition("values")
        text = text.strip()
    if text.startswith("(") and text.endswith(")"):
        text = text[1:-1]

    items = text.split(",")
    values: List[Any] = []
    for item in items:
        item = item.strip()
        if not item:
            continue
        values.append(_convert_literal(item))
    return values


def parse_condition(condition: str) -> Dict[str, Any]:
    if "=" not in condition:
        raise ValueError(f"Некорректное значение: {condition}. Попробуйте снова.")
    left, right = condition.split("=", 1)
    column = left.strip()
    raw_value = right.strip()
    if not column or not raw_value:
        raise ValueError(f"Некорректное значение: {condition}. Попробуйте снова.")
    value = _convert_literal(raw_value)
    return {column: value}


def parse_insert_command(command: str) -> tuple[str, List[Any]]:
    lower = command.lower()
    if "values" not in lower:
        raise ValueError("Некорректное значение: отсутствует VALUES. Попробуйте снова.")

    before_values, _, after_values = command.partition("values")
    parts = before_values.strip().split()
    if len(parts) < 3:
        raise ValueError("Некорректное значение: некорректная команда insert.")
    table_name = parts[2]
    values = parse_values_part(after_values)
    return table_name, values


def parse_select_command(command: str) -> tuple[str, Dict[str, Any] | None]:
    lower = command.lower()
    if " from " not in lower:
        raise ValueError("Некорректная команда select.")
    if " where " in lower:
        before_where, _, where_part = command.partition(" where ")
        parts = before_where.strip().split()
        if len(parts) < 3:
            raise ValueError("Некорректная команда select.")
        table_name = parts[2]
        where_clause = parse_condition(where_part)
    else:
        parts = command.strip().split()
        if len(parts) < 3:
            raise ValueError("Некорректная команда select.")
        table_name = parts[2]
        where_clause = None
    return table_name, where_clause


def parse_update_command(
    command: str,
) -> tuple[str, Dict[str, Any], Dict[str, Any]]:
    lower = command.lower()
    if " set " not in lower or " where " not in lower:
        raise ValueError("Некорректная команда update.")

    _, _, after_update = command.partition(" ")
    table_name, _, rest = after_update.partition(" set ")
    set_part, _, where_part = rest.partition(" where ")

    table_name = table_name.strip()
    if not table_name:
        raise ValueError("Некорректная команда update.")
    set_clause = parse_condition(set_part)
    where_clause = parse_condition(where_part)
    return table_name, set_clause, where_clause


def parse_delete_command(command: str) -> tuple[str, Dict[str, Any]]:
    lower = command.lower()
    if not lower.startswith("delete from"):
        raise ValueError("Некорректная команда delete.")
    _, _, after_from = command.partition("from")
    before_where, _, where_part = after_from.partition(" where ")
    table_name = before_where.strip()
    if not table_name:
        raise ValueError("Некорректная команда delete.")
    where_clause = parse_condition(where_part)
    return table_name, where_clause
