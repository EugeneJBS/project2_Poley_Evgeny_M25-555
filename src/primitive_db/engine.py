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

SELECT_CACHE = create_cacher()


def print_help() -> None:
    print("\n***Процесс работы с таблицей***")
    print("Функции:")
    print("<command> create_table <имя_таблицы> <столбец1:тип> .. - создать таблицу")
    print("<command> list_tables - показать список всех таблиц")
    print("<command> drop_table <имя_таблицы> - удалить таблицу")

    print("\n***Операции с данными***")
    print(
        "<command> insert into <имя_таблицы> values "
        "(<значение1>, <значение2>, ...) - создать запись."
    )
    print(
        "<command> select from <имя_таблицы> where <столбец> = <значение> "
        "- прочитать записи по условию."
    )
    print("<command> select from <имя_таблицы> - прочитать все записи.")
    print(
        "<command> update <имя_таблицы> set <столбец1> = <новое_значение1> "
        "where <столбец_условия> = <значение_условия> - обновить запись."
    )
    print(
        "<command> delete from <имя_таблицы> where <столбец> = <значение> "
        "- удалить запись."
    )
    print("<command> info <имя_таблицы> - вывести информацию о таблице.")

    print("\nОбщие команды:")
    print("<command> exit - выход из программы")
    print("<command> help - справочная информация\n")


def welcome() -> None:
    name = prompt.string("Пожалуйста, введите свое имя ")
    if not name:
        name = "user"

    print(f"Привет, {name}!")
    print("***")
    print("<command> exit - выйти из программы")
    print("<command> help - справочная информация")
    print("Введите команду: help\n")


@handle_db_errors
def handle_create_table(tokens: list[str]) -> None:
    if len(tokens) < 3:
        raise ValueError(
            "Некорректное значение: недостаточно аргументов. Попробуйте снова.",
        )

    table_name = tokens[1]
    columns_tokens = tokens[2:]
    columns = db_parser.parse_columns(columns_tokens)

    metadata = load_metadata(META_FILE)
    metadata = core.create_table(metadata, table_name, columns)
    save_metadata(META_FILE, metadata)

    columns_info = metadata[table_name]["columns"]
    cols_as_str = ", ".join(
        f'{c["name"]}:{c["type"]}' for c in columns_info
    )
    print(
        f'Таблица "{table_name}" успешно создана '
        f"со столбцами: {cols_as_str}",
    )


@handle_db_errors
@confirm_action("удаление таблицы")
def handle_drop_table(tokens: list[str]) -> None:
    if len(tokens) != 2:
        raise ValueError(
            "Некорректное значение: нужно указать имя таблицы. "
            "Попробуйте снова.",
        )

    table_name = tokens[1]
    metadata = load_metadata(META_FILE)
    metadata = core.drop_table(metadata, table_name)
    save_metadata(META_FILE, metadata)
    print(f'Таблица "{table_name}" успешно удалена.')


@handle_db_errors
def handle_list_tables() -> None:
    metadata = load_metadata(META_FILE)
    if not metadata:
        print("Таблиц пока нет.")
        return

    for name in metadata:
        print(f"- {name}")


@handle_db_errors
@log_time
def handle_insert(command: str) -> None:
    table_name, values = db_parser.parse_insert_command(command)

    metadata = load_metadata(META_FILE)
    table_data = load_table_data(table_name)
    table_data, new_id = core.insert_row(metadata, table_name, values, table_data)
    save_table_data(table_name, table_data)
    print(
        f'Запись с ID={new_id} успешно добавлена в таблицу "{table_name}".',
    )


@handle_db_errors
@log_time
def handle_select(command: str) -> None:
    table_name, where_clause = db_parser.parse_select_command(command)

    def compute():
        metadata = load_metadata(META_FILE)
        table_data = load_table_data(table_name)
        return core.select_rows(metadata, table_name, table_data, where_clause)

    cache_key = (table_name, None)
    if where_clause:
        cache_key = (table_name, tuple(sorted(where_clause.items())))

    rows = SELECT_CACHE(cache_key, compute)
    if not rows:
        print("Записей не найдено.")
        return

    field_names = list(rows[0].keys())
    table = PrettyTable()
    table.field_names = field_names
    for row in rows:
        table.add_row([row.get(name, "") for name in field_names])

    print(table)


@handle_db_errors
@log_time
def handle_update(command: str) -> None:
    table_name, set_clause, where_clause = db_parser.parse_update_command(command)

    metadata = load_metadata(META_FILE)
    table_data = load_table_data(table_name)
    table_data, updated_ids = core.update_rows(
        metadata,
        table_name,
        table_data,
        set_clause,
        where_clause,
    )
    save_table_data(table_name, table_data)

    if not updated_ids:
        print("Подходящих записей не найдено.")
        return

    ids_str = ", ".join(str(x) for x in updated_ids)
    print(
        f"Записи с ID={ids_str} в таблице "
        f'"{table_name}" успешно обновлены.',
    )


@handle_db_errors
@confirm_action("удаление записей")
@log_time
def handle_delete(command: str) -> None:
    table_name, where_clause = db_parser.parse_delete_command(command)

    metadata = load_metadata(META_FILE)
    table_data = load_table_data(table_name)
    table_data, deleted_ids = core.delete_rows(
        metadata,
        table_name,
        table_data,
        where_clause,
    )
    save_table_data(table_name, table_data)

    if not deleted_ids:
        print("Подходящих записей не найдено.")
        return

    ids_str = ", ".join(str(x) for x in deleted_ids)
    print(
        f"Записи с ID={ids_str} успешно удалены "
        f'из таблицы "{table_name}".',
    )


@handle_db_errors
def handle_info(tokens: list[str]) -> None:
    if len(tokens) != 2:
        raise ValueError(
            "Некорректное значение: нужно указать имя таблицы. "
            "Попробуйте снова.",
        )

    table_name = tokens[1]
    metadata = load_metadata(META_FILE)
    table_data = load_table_data(table_name)
    info = core.get_table_info(metadata, table_name, table_data)
    print(info)


def run() -> None:
    while True:
        try:
            user_input = input("Введите команду: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nВыход.")
            break

        if not user_input:
            continue

        lower = user_input.lower()

        if lower in {"exit", "quit"}:
            print("Выход из программы.")
            break

        if lower == "help":
            print_help()
            continue

        tokens = shlex.split(user_input)
        if not tokens:
            continue

        command = tokens[0]

        if command == "create_table":
            handle_create_table(tokens)
        elif command == "list_tables":
            handle_list_tables()
        elif command == "drop_table":
            handle_drop_table(tokens)
        elif lower.startswith("insert into"):
            handle_insert(user_input)
        elif lower.startswith("select"):
            handle_select(user_input)
        elif lower.startswith("update"):
            handle_update(user_input)
        elif lower.startswith("delete"):
            handle_delete(user_input)
        elif command == "info":
            handle_info(tokens)
        else:
            print(f"Функции {command} нет. Попробуйте снова.")
