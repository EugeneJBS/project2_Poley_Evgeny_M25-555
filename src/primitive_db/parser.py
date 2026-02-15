"""
Функции для разбора сложных команд (where, set, values) через shlex.
"""

import shlex
from typing import Any, Dict, List, Tuple


def _convert_literal(val: str) -> Any:
    """Преобразует строковый литерал в тип Python."""
    val = val.strip()
    # Обработка строк в кавычках
    if val.startswith('"') and val.endswith('"'):
        return val[1:-1]
    # Обработка булевых значений
    if val.lower() == "true":
        return True
    if val.lower() == "false":
        return False
    # Обработка чисел
    if val.isdigit():
        return int(val)
    return val


def parse_columns(tokens: List[str]) -> List[Tuple[str, str]]:
    """Парсит токены столбцов вида ['name:str', 'age:int']."""
    res = []
    for t in tokens:
        if ":" not in t:
            raise ValueError(f"Некорректное значение: {t}. Ожидалось 'имя:тип'.")
        name, c_type = t.split(":", 1)
        res.append((name.strip(), c_type.strip()))
    return res


def parse_condition(tokens: List[str]) -> Dict[str, Any]:
    """Преобразует часть токенов ['age', '=', '25'] в словарь {'age': 25}."""
    if len(tokens) < 3 or tokens[1] != "=":
        raise ValueError("Некорректное условие. Используйте формат 'поле = значение'.")
    return {tokens[0]: _convert_literal(tokens[2])}


def parse_insert_command(command: str) -> Tuple[str, List[Any]]:
    """Разбирает команду INSERT."""
    tokens = shlex.split(command)
    if len(tokens) < 5 or tokens[3].lower() != "values":
        raise ValueError("Ошибка в синтаксисе INSERT. Используйте: insert into <table> values (...)")

    table_name = tokens[2]
    # Собираем значения, игнорируя возможные скобки, если они попали в токены
    values = [_convert_literal(v.strip("(),")) for v in tokens[4:]]
    return table_name, values


def parse_select_command(command: str) -> Tuple[str, Dict[str, Any] | None]:
    """Разбирает команду SELECT."""
    tokens = shlex.split(command)
    table_name = tokens[2]
    where_clause = None

    if "where" in [t.lower() for t in tokens]:
        where_idx = [t.lower() for t in tokens].index("where")
        where_clause = parse_condition(tokens[where_idx + 1:])

    return table_name, where_clause


def parse_update_command(command: str) -> Tuple[str, Dict[str, Any], Dict[str, Any]]:
    """Разбирает команду UPDATE."""
    tokens = shlex.split(command)
    table_name = tokens[1]

    low_tokens = [t.lower() for t in tokens]
    set_idx = low_tokens.index("set")
    where_idx = low_tokens.index("where")

    set_clause = parse_condition(tokens[set_idx + 1 : where_idx])
    where_clause = parse_condition(tokens[where_idx + 1 :])

    return table_name, set_clause, where_clause


def parse_delete_command(command: str) -> Tuple[str, Dict[str, Any]]:
    """Разбирает команду DELETE."""
    tokens = shlex.split(command)
    table_name = tokens[2]

    low_tokens = [t.lower() for t in tokens]
    where_idx = low_tokens.index("where")
    where_clause = parse_condition(tokens[where_idx + 1:])

    return table_name, where_clause
