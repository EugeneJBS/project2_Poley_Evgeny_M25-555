"""
Модуль отвечает за запуск, цикл и парсинг команд.
"""

import shlex

import prompt
from prettytable import PrettyTable

from . import core
from . import parser as db_parser
from .constants import META_FILE
from .decorators import (
    confirm_action,
    create_cacher,
    handle_db_errors,
    log_time,
)
from .utils import (
    load_metadata,
    load_table_data,
    save_metadata,
    save_table_data,
)

# Кэш для операций SELECT (реализация через замыкание)
SELECT_CACHE = create_cacher()


def print_help() -> None:
    """Выводит справочную информацию."""
    print("\n***Процесс работы с таблицей***")
    print("Функции:")
    print("<command> create_table <имя_таблицы> <столбец1:тип> .. - создать таблицу")
    print("<command> list_tables - показать список всех таблиц")
    print("<command> drop_table <имя_таблицы> - удалить таблицу")

    print("\n***Операции с данными***")
    msg_insert = "<command> insert into <имя_таблицы> values (<значение1>, ..)"
    print(f"{msg_insert} - создать запись.")
    print("<command> select from <имя_таблицы> where <столбец> = <значение>")
    print("<command> select from <имя_таблицы> - прочитать все записи.")
    msg_upd = "<command> update <имя_таблицы> set <столб1> = <знач1> where .."
    print(f"{msg_upd} - обновить запись.")
    print("<command> delete from <имя_таблицы> where <столбец> = <значение>")
    print("<command> info <имя_таблицы> - вывести информацию о таблице.")

    print("\nОбщие команды:")
    print("<command> exit - выйти из программы")
    print("<command> help - справочная информация\n")


def welcome() -> None:
    """Приветствие пользователя."""
    print("***")
    print("<command> exit - выйти из программы")
    print("<command> help - справочная информация")
    print("Введите команду: help")


@handle_db_errors
def handle_create_table(tokens: list[str]) -> None:
    """Обработчик команды создания таблицы."""
    if len(tokens) < 3:
        raise ValueError("Некорректное значение. Попробуйте снова.")

    table_name = tokens[1]
    columns = db_parser.parse_columns(tokens[2:])

    metadata = load_metadata(META_FILE)
    metadata = core.create_table(metadata, table_name, columns)
    save_metadata(META_FILE, metadata)

    cols_info = metadata[table_name]["columns"]
    cols_str = ", ".join(f"{c['name']}:{c['type']}" for c in cols_info)
    print(f'Таблица "{table_name}" успешно создана со столбцами: {cols_str}')


@handle_db_errors
@confirm_action("удаление таблицы")
def handle_drop_table(tokens: list[str]) -> None:
    """Обработчик команды удаления таблицы."""
    if len(tokens) != 2:
        raise ValueError("Нужно указать имя таблицы.")

    table_name = tokens[1]
    metadata = load_metadata(META_FILE)
    metadata = core.drop_table(metadata, table_name)
    save_metadata(META_FILE, metadata)
    print(f'Таблица "{table_name}" успешно удалена.')


@handle_db_errors
def handle_list_tables() -> None:
    """Выводит список таблиц."""
    metadata = load_metadata(META_FILE)
    if not metadata:
        print("Таблиц пока нет.")
        return
    for name in metadata:
        print(f"- {name}")


@handle_db_errors
@log_time
def handle_insert(user_input: str) -> None:
    """Добавляет запись в таблицу."""
    table_name, values = db_parser.parse_insert_command(user_input)
    metadata = load_metadata(META_FILE)
    table_data = load_table_data(table_name)

    table_data, new_id = core.insert_row(metadata, table_name, values, table_data)
    save_table_data(table_name, table_data)
    print(f'Запись с ID={new_id} успешно добавлена в таблицу "{table_name}".')


@handle_db_errors
@log_time
def handle_select(user_input: str) -> None:
    """Выбирает и выводит данные с использованием PrettyTable и кэша."""
    table_name, where_clause = db_parser.parse_select_command(user_input)

    def fetch_data():
        table_data = load_table_data(table_name)
        return core.select_rows(table_data, where_clause)

    # Используем замыкание для кэширования
    rows = SELECT_CACHE(user_input, fetch_data)

    if not rows:
        print("Записей не найдено.")
        return

    table = PrettyTable()
    table.field_names = rows[0].keys()
    for row in rows:
        table.add_row(row.values())
    print(table)


@handle_db_errors
@log_time
def handle_update(user_input: str) -> None:
    """Обновляет существующие записи."""
    table_name, set_cl, where_cl = db_parser.parse_update_command(user_input)
    metadata = load_metadata(META_FILE)
    table_data = load_table_data(table_name)

    table_data, updated_ids = core.update_rows(
        metadata, table_name, table_data, set_cl, where_cl
    )
    save_table_data(table_name, table_data)

    if updated_ids:
        ids_str = ", ".join(map(str, updated_ids))
        print(f'Запись с ID={ids_str} в таблице "{table_name}" успешно обновлена.')


@handle_db_errors
@confirm_action("удаление записи")
@log_time
def handle_delete(user_input: str) -> None:
    """Удаляет записи по условию."""
    table_name, where_clause = db_parser.parse_delete_command(user_input)
    metadata = load_metadata(META_FILE)
    table_data = load_table_data(table_name)

    new_data, deleted_ids = core.delete_rows(
        metadata, table_name, table_data, where_clause
    )
    save_table_data(table_name, new_data)

    if deleted_ids:
        ids_str = ", ".join(map(str, deleted_ids))
        print(f'Запись с ID={ids_str} успешно удалена из таблицы "{table_name}".')


@handle_db_errors
def handle_info(tokens: list[str]) -> None:
    """Выводит структуру таблицы и количество записей."""
    if len(tokens) < 2:
        raise ValueError("Нужно указать имя таблицы.")
    table_name = tokens[1]
    metadata = load_metadata(META_FILE)
    table_data = load_table_data(table_name)

    info_text = core.get_table_info(metadata, table_name, table_data)
    print(info_text)


def run() -> None:
    """Основной цикл обработки команд."""
    while True:
        try:
            user_input = prompt.string(">>>Введите команду: ")
        except (EOFError, KeyboardInterrupt):
            break

        if not user_input:
            continue

        low_input = user_input.lower()
        if low_input == "exit":
            break
        if low_input == "help":
            print_help()
            continue

        tokens = shlex.split(user_input)
        command = tokens[0]

        if command == "create_table":
            handle_create_table(tokens)
        elif command == "list_tables":
            handle_list_tables()
        elif command == "drop_table":
            handle_drop_table(tokens)
        elif low_input.startswith("insert into"):
            handle_insert(user_input)
        elif low_input.startswith("select"):
            handle_select(user_input)
        elif low_input.startswith("update"):
            handle_update(user_input)
        elif low_input.startswith("delete"):
            handle_delete(user_input)
        elif command == "info":
            handle_info(tokens)
        else:
            print(f"Функции {command} нет. Попробуйте снова.")
