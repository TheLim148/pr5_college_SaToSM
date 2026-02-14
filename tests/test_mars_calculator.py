import pytest

from pr5.mars_calculator import MarsCalculator


@pytest.fixture()
def calc():
    return MarsCalculator()


def test_add(calc):
    assert calc.add(2, 3) == 5
    assert calc.add(-2, 3) == 1
    assert calc.add(0, 0) == 0


def test_divide(calc):
    assert calc.divide(10, 2) == 5
    assert calc.divide(5, 2) == 2.5
    assert calc.divide(-10, 2) == -5
    with pytest.raises(ZeroDivisionError):
        calc.divide(1, 0)


def test_power_requires_int_exponent(calc):
    assert calc.power(2, 3) == 8
    assert calc.power(2, 0) == 1
    assert calc.power(2, -1) == 0.5
    with pytest.raises(TypeError):
        calc.power(2, 0.5)
    with pytest.raises(TypeError):
        calc.power(2, "3")


@pytest.mark.parametrize(
    "n, expected",
    [(0, 1), (1, 1), (2, 2), (3, 6), (5, 120), (10, 3628800)],
)
def test_factorial_valid(calc, n, expected):
    assert calc.factorial(n) == expected


def test_factorial_negative(calc):
    with pytest.raises(ValueError, match="отрицательного"):
        calc.factorial(-1)


def test_factorial_too_large(calc):
    with pytest.raises(ValueError, match="Слишком большое"):
        calc.factorial(11)


def test_factorial_requires_int(calc):
    with pytest.raises(TypeError):
        calc.factorial(3.2)
    with pytest.raises(TypeError):
        calc.factorial("3")
