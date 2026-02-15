#!/usr/bin/env python3
"""
Точка входа в приложение Primitive DB.
"""

from src.primitive_db.engine import run, welcome


def main() -> None:
    """Запуск приветствия и основного цикла программы."""
    print("Проект запущен!")
    welcome()
    run()


if __name__ == "__main__":
    main()
