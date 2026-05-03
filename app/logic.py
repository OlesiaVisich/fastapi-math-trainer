"""Логика генерации математических заданий."""
import random
from fractions import Fraction
from typing import List
from app.schemas import TaskSchema


def format_number(n, is_first=False):
    """Форматирует число: отрицательные оборачивает в скобки."""
    if isinstance(n, Fraction):
        if n.denominator == 1:
            return str(n.numerator)
        return f"{n.numerator}/{n.denominator}"
    if isinstance(n, float):
        s = f"{n:.1f}".replace(".", ",")
        return s
    if n < 0 and not is_first:
        return f"({n})"
    return str(n)


def generate_numbers_for_type(
    number_type: str, min_val: int, max_val: int
) -> tuple:
    """Генерирует два числа в зависимости от типа."""
    if number_type == "natural":
        a = random.randint(max(1, min_val), max_val)
        b = random.randint(max(1, min_val), max_val)
    elif number_type == "integer":
        a = random.randint(min_val, max_val)
        b = random.randint(min_val, max_val)
    elif number_type == "fraction":
        target_value = random.uniform(float(min_val), float(max_val))
        a = Fraction(target_value).limit_denominator(100)
        target_value2 = random.uniform(float(min_val), float(max_val))
        b = Fraction(target_value2).limit_denominator(100)
    elif number_type == "decimal":
        a = round(random.uniform(0.1, float(max_val)), 1)
        b = round(random.uniform(0.1, float(max_val)), 1)
        if random.random() < 0.3:
            a = round(random.uniform(0.01, 0.9), 2)
        if random.random() < 0.3:
            b = round(random.uniform(0.01, 0.9), 2)
    else:
        a = random.randint(min_val, max_val)
        b = random.randint(min_val, max_val)
    return a, b


def generate_tasks(
    number_type: str,
    operations: list,
    min_num: int,
    max_num: int,
    count: int,
    only_positive_answers: bool = False,
    numbered_tasks: bool = False,
) -> List[TaskSchema]:
    """Генерирует список заданий по параметрам."""
    tasks = []
    for i in range(count):
        op = random.choice(operations)
        while True:
            a, b = generate_numbers_for_type(number_type, min_num, max_num)

            if op == "+":
                ans = a + b
            elif op == "-":
                ans = a - b
            elif op == "*":
                ans = a * b
            else:  # '/'
                if isinstance(a, Fraction) or isinstance(b, Fraction):
                    if b == 0:
                        continue
                    ans = a / b
                elif isinstance(a, float) or isinstance(b, float):
                    if b == 0:
                        continue
                    ans = a / b
                else:
                    if (
                        number_type == "integer"
                        and not isinstance(a, Fraction)
                        and not isinstance(a, float)
                    ):
                        b = (
                            random.randint(max(1, min_num), max_val)
                            if max_val > 0
                            else random.randint(1, 10)
                        )
                        ans_int = random.randint(min_num, max_num)
                        a = b * ans_int
                        ans = a // b
                    else:
                        if b == 0:
                            continue
                        ans = a / b

            if only_positive_answers and float(ans) < 0:
                continue

            break

        q = f"{format_number(a, is_first=True)} {op} {format_number(b)} = ?"
        if numbered_tasks:
            q = f"{i+1}) {q}"

        tasks.append(TaskSchema(question=q, answer=str(ans), order_index=i))

    return tasks