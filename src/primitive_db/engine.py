"""
Модуль отвечает за запуск, цикл и парсинг команд.
"""

import shlex
import prompt

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

# Кэш для операций SELECT
SELECT_CACHE = create_cacher()


def print_help() -> None:
    """Выводит справочную информацию."""
    print("\n***Процесс работы с таблицей***")
    print("Функции:")
    print("<command> create_table <имя_таблицы> <столбец1:тип> .. - создать таблицу")
    print("<command> list_tables - показать список всех таблиц")
    print("<command> drop_table <имя_таблицы> - удалить таблицу")

    print("\n***Операции с данными***")
    print("<command> insert into <имя_таблицы> values (<значение1>, ..) - создать запись.")
    print("<command> select from <имя_таблицы> where <столбец> = <значение>")
    print("<command> select from <имя_таблицы> - прочитать все записи.")
    print("<command> update <имя_таблицы> set <столбец1> = <значение> where ..")
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
    columns_tokens = tokens[2:]
    columns = db_parser.parse_columns(columns_tokens)

    metadata = load_metadata(META_FILE)
    metadata = core.create_table(metadata, table_name, columns)
    save_metadata(META_FILE, metadata)

    # Вывод: Таблица "users" успешно создана
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


def run() -> None:
    """Основной цикл обработки команд."""
    while True:
        try:
            # prompt для ввода
            user_input = prompt.string(">>>Введите команду: ")
        except (EOFError, KeyboardInterrupt):
            break

        if not user_input:
            continue

        if user_input.lower() == "exit":
            break
        if user_input.lower() == "help":
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
        elif command == "exit":
            break
        # Остальные команды (insert, select и т.д.) будут добавлены позже
        else:
            print(f"Функции {command} нет. Попробуйте снова.")