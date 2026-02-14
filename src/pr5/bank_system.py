from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, List, Optional, Tuple


SUPPORTED_CURRENCIES = {"RUB", "USD", "EUR", "GBP"}
_MONEY_Q = Decimal("0.01")


def _to_decimal_money(value) -> Decimal:
    """Преобразует введённое значение в денежное десятичное с двумя знаками после запятой.

    - Отвергает bool
    - Принимает int / float / Decimal
    - Округляет используя ROUND_HALF_UP
    """
    if isinstance(value, bool):
        raise TypeError("amount должен быть числом")
    if not isinstance(value, (int, float, Decimal)):
        raise TypeError("amount должен быть числом")
    return Decimal(str(value)).quantize(_MONEY_Q, rounding=ROUND_HALF_UP)


class CurrencyConverter:
    """Простой конвертер валют"""

    def __init__(self, rates: Optional[Dict[Tuple[str, str], Decimal]] = None):
        self._rates: Dict[Tuple[str, str], Decimal] = rates or {
            ("RUB", "USD"): Decimal("0.01"),
            ("USD", "RUB"): Decimal("100"),
            ("RUB", "EUR"): Decimal("0.0090909091"),
            ("EUR", "RUB"): Decimal("110"),
            ("RUB", "GBP"): Decimal("0.0076923077"),
            ("GBP", "RUB"): Decimal("130"),
        }

    def convert(self, amount: Decimal, from_currency: str, to_currency: str) -> Decimal:
        if from_currency not in SUPPORTED_CURRENCIES:
            raise ValueError("Неподдерживаемая валюта")
        if to_currency not in SUPPORTED_CURRENCIES:
            raise ValueError("Неподдерживаемая валюта")

        if not isinstance(amount, Decimal):
            raise TypeError("amount должен быть Decimal")

        amount = amount.quantize(_MONEY_Q, rounding=ROUND_HALF_UP)

        if from_currency == to_currency:
            return amount

        key = (from_currency, to_currency)
        if key not in self._rates:
            raise ValueError(f"Неподдерживаемая конвертация: {from_currency}->{to_currency}")

        return (amount * self._rates[key]).quantize(_MONEY_Q, rounding=ROUND_HALF_UP)


class BankAccount:
    """Bank account с поддержкой множества валют и историей транзакций"""

    MAX_DEPOSIT = Decimal("1000000.00")

    def __init__(self, owner: str, balance=0, currency: str = "RUB"):
        if not isinstance(owner, str) or not owner.strip():
            raise ValueError("owner должен быть не пустой строкой")
        if currency not in SUPPORTED_CURRENCIES:
            raise ValueError("Неподдерживаемая валюта")

        self.owner = owner
        self.balance: Decimal = _to_decimal_money(balance)
        self.currency = currency

        self.transactions: List[str] = []
        self.is_blocked = False
        self.overdraft_limit: Decimal = Decimal("0.00")

    def deposit(self, amount):
        """Депозит на счёт"""
        amount_d = _to_decimal_money(amount)
        if amount_d <= 0:
            raise ValueError("Депозит должен быть позитивным")
        if amount_d > self.MAX_DEPOSIT:
            raise ValueError("Депозит слишком велик")

        self.balance = (self.balance + amount_d).quantize(_MONEY_Q, rounding=ROUND_HALF_UP)
        self.transactions.append(f"+{amount_d} {self.currency}")
        return self.balance

    def withdraw(self, amount):
        """Снятие денег с комиссией 1%."""
        if self.is_blocked:
            raise PermissionError("Аккаунт заблокирован")

        amount_d = _to_decimal_money(amount)
        if amount_d <= 0:
            raise ValueError("Снятие должно быть позитивным")

        fee = (amount_d * Decimal("0.01")).quantize(_MONEY_Q, rounding=ROUND_HALF_UP)
        total = amount_d + fee

        if self.balance - total < -self.overdraft_limit:
            raise ValueError("Недостаток средств")

        self.balance = (self.balance - total).quantize(_MONEY_Q, rounding=ROUND_HALF_UP)
        self.transactions.append(f"-{amount_d} (комиссия: {fee}) {self.currency}")
        return amount_d

    def convert_to(self, target_currency: str, converter: Optional[CurrencyConverter] = None):
        """Конвертация денег с одной валюты в другую"""
        if target_currency not in SUPPORTED_CURRENCIES:
            raise ValueError("Неподдерживаемая валюта")
        converter = converter or CurrencyConverter()

        self.balance = converter.convert(self.balance, self.currency, target_currency)
        self.currency = target_currency
        self.transactions.append(f"Конвертировать в {target_currency}")
        return self.balance

    def get_statement(self):
        """Возвращает снимок состояния оператора"""
        return {
            "owner": self.owner,
            "currency": self.currency,
            "balance": self.balance,
            "transactions": list(self.transactions),
            "is_blocked": self.is_blocked,
        }

    def transfer(
        self,
        target_account: "BankAccount",
        amount,
        converter: Optional[CurrencyConverter] = None,
    ):
        """Перенос денег на другой аккаунт"""
        if self.is_blocked:
            raise PermissionError("Аккаунт заблокирован")
        if target_account is None or not isinstance(target_account, BankAccount):
            raise TypeError("target_account должен быть BankAccount")

        amount_d = _to_decimal_money(amount)
        if amount_d <= 0:
            raise ValueError("Количество передаваемых денег должно быть позитивным")

        converter = converter or CurrencyConverter()

        if self.balance - amount_d < -self.overdraft_limit:
            raise ValueError("Недостаток средств")

        credited = converter.convert(amount_d, self.currency, target_account.currency)

        self.balance = (self.balance - amount_d).quantize(_MONEY_Q, rounding=ROUND_HALF_UP)
        target_account.balance = (target_account.balance + credited).quantize(_MONEY_Q, rounding=ROUND_HALF_UP)

        self.transactions.append(f"Передача -{amount_d} {self.currency} в {target_account.owner}")
        target_account.transactions.append(f"Передача +{credited} {target_account.currency} от {self.owner}")
        return credited


class Bank:
    """Банк управляющий множеством аккаунтов"""

    def __init__(self, name: str):
        if not isinstance(name, str) or not name.strip():
            raise ValueError("name должно быть не пустой строкой")
        self.name = name
        self.accounts: Dict[str, BankAccount] = {}

    def create_account(self, owner: str, initial_balance=0, currency: str = "RUB"):
        if owner in self.accounts:
            raise ValueError("Такой аккаунт уже существует")
        account = BankAccount(owner, initial_balance, currency)
        self.accounts[owner] = account
        return account

    def total_deposits(self, currency: str = "RUB", converter: Optional[CurrencyConverter] = None):
        if currency not in SUPPORTED_CURRENCIES:
            raise ValueError("Неподдерживаемая валюта")
        converter = converter or CurrencyConverter()

        total = Decimal("0.00")
        for acc in self.accounts.values():
            if acc.is_blocked:
                continue
            total += converter.convert(acc.balance, acc.currency, currency)

        return total.quantize(_MONEY_Q, rounding=ROUND_HALF_UP)
