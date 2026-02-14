from __future__ import annotations

from math import prod


class MarsCalculator:
    """Калькулятор для марсохода NASA"""

    def add(self, a, b):
        return a + b

    def divide(self, a, b):
        if b == 0:
            raise ZeroDivisionError("Деление на ноль приведет к провалу миссии")
        return a / b

    def power(self, a, b):
        # По ТЗ: b — целое
        if not isinstance(b, int):
            raise TypeError("b must be int")
        return a ** b

    def factorial(self, n):
        # Спецификация из задания:
        # n in [0..10] -> значение
        # n > 10 -> ValueError("Слишком большое число для бортового компьютера")
        # n < 0 -> ValueError("Факториал отрицательного числа не определен")
        if not isinstance(n, int):
            raise TypeError("n должен быть int")

        if n < 0:
            raise ValueError("Факториал отрицательного числа не определен")
        if n > 10:
            raise ValueError("Слишком большое число для бортового компьютера")
        if n in (0, 1):
            return 1
        return prod(range(2, n + 1))
