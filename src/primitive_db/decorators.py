"""
Декораторы для обработки ошибок, подтверждения действий,
логирования времени выполнения и механизм кэширования через замыкания.
"""

import functools
import time
from typing import Any, Callable, Dict

# Тип для декорируемых функций
FuncType = Callable[..., Any]


def handle_db_errors(func: FuncType) -> FuncType:
    """Декоратор для обработки исключений БД."""
    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        try:
            return func(*args, **kwargs)
        except FileNotFoundError:
            print("Ошибка: Файл данных не найден. "
            "Возможно, база данных не инициализирована."
            )
        except KeyError as e:
            print(f"Ошибка: Таблица или столбец {e} не найден.")
        except ValueError as e:
            print(f"Ошибка валидации: {e}")
        except Exception as e:
            print(f"Произошла непредвиденная ошибка: {e}")
        return None
    return wrapper


def confirm_action(action_name: str) -> Callable[[FuncType], FuncType]:
    """Декоратор для подтверждения опасных операций (удаление)."""
    def decorator(func: FuncType) -> FuncType:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            prompt_text = f'Вы уверены, что хотите выполнить "{action_name}"? [y/n]: '
            answer = input(prompt_text).strip().lower()
            if answer != "y":
                print("Операция отменена.")
                return None
            return func(*args, **kwargs)
        return wrapper
    return decorator


def log_time(func: FuncType) -> FuncType:
    """Декоратор для замера времени выполнения функции."""
    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        start = time.monotonic()
        result = func(*args, **kwargs)
        elapsed = time.monotonic() - start
        print(f"Функция {func.__name__} выполнилась за {elapsed:.3f} секунд.")
        return result
    return wrapper


def create_cacher() -> Callable[[Any, Callable[[], Any]], Any]:
    """Реализация кэширования через замыкание."""
    cache: Dict[Any, Any] = {}

    def cache_result(key: Any, value_func: Callable[[], Any]) -> Any:
        """Проверяет наличие результата в кэше."""
        if key in cache:
            return cache[key]
        value = value_func()
        cache[key] = value
        return value

    return cache_result
