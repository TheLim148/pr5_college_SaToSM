import pytest
from decimal import Decimal

from pr5.bank_system import Bank, BankAccount, CurrencyConverter, _to_decimal_money


@pytest.fixture()
def converter_1to1():
    # простой конвертер 1:1 (для изоляции логики переводов от курсов)
    class Stub(CurrencyConverter):
        def convert(self, amount, from_currency, to_currency):
            return amount
    return Stub()


def test_to_decimal_money_rejects_bool_and_rounds():
    with pytest.raises(TypeError):
        _to_decimal_money(True)
    assert _to_decimal_money(1) == Decimal("1.00")
    assert _to_decimal_money(1.005) == Decimal("1.01")  # ROUND_HALF_UP


def test_account_init_validates_owner_and_currency():
    with pytest.raises(ValueError):
        BankAccount("", 0, "RUB")
    with pytest.raises(ValueError):
        BankAccount("Alice", 0, "AAA")


def test_currency_converter_convert_validates_input():
    conv = CurrencyConverter({("USD", "RUB"): Decimal("100")})
    with pytest.raises(ValueError):
        conv.convert(Decimal("1.00"), "AAA", "RUB")
    with pytest.raises(ValueError):
        conv.convert(Decimal("1.00"), "USD", "AAA")
    with pytest.raises(TypeError):
        conv.convert(1, "USD", "RUB")  # amount must be Decimal

    assert conv.convert(Decimal("1.00"), "USD", "USD") == Decimal("1.00")
    assert conv.convert(Decimal("1.23"), "USD", "RUB") == Decimal("123.00")  # quantize


def test_deposit_rejects_negative_zero_non_number_and_too_large():
    acc = BankAccount("Alice", 0, "RUB")
    with pytest.raises(ValueError):
        acc.deposit(-1)
    with pytest.raises(ValueError):
        acc.deposit(0)
    with pytest.raises(TypeError):
        acc.deposit("100")
    with pytest.raises(ValueError):
        acc.deposit(10**9)  # too large


def test_deposit_applies_and_records_transaction():
    acc = BankAccount("Alice", 0, "RUB")
    acc.deposit(10)
    assert acc.balance == Decimal("10.00")
    assert acc.transactions[-1] == "+10.00 RUB"


def test_withdraw_blocked_account():
    acc = BankAccount("Alice", 100, "RUB")
    acc.is_blocked = True
    with pytest.raises(PermissionError):
        acc.withdraw(10)


def test_withdraw_rejects_negative_and_zero():
    acc = BankAccount("Alice", 100, "RUB")
    with pytest.raises(ValueError):
        acc.withdraw(0)
    with pytest.raises(ValueError):
        acc.withdraw(-1)


def test_withdraw_checks_funds_and_fee():
    acc = BankAccount("Alice", 100, "RUB")
    returned = acc.withdraw(10)
    assert returned == Decimal("10.00")
    # fee 0.10, total 10.10
    assert acc.balance == Decimal("89.90")
    assert acc.transactions[-1] == "-10.00 (fee: 0.10) RUB"


def test_withdraw_insufficient_funds():
    acc = BankAccount("Alice", 10, "RUB")
    with pytest.raises(ValueError):
        acc.withdraw(10)  # total 10.10 > 10.00


def test_convert_to_changes_currency_and_uses_converter(converter_1to1):
    acc = BankAccount("Alice", 100, "RUB")
    acc.deposit(1)
    acc.convert_to("USD", converter=converter_1to1)
    assert acc.currency == "USD"
    assert acc.balance == Decimal("101.00")
    assert acc.transactions[-1] == "Convert to USD"


def test_get_statement_is_snapshot_copy():
    acc = BankAccount("Alice", 0, "RUB")
    acc.deposit(1)
    st = acc.get_statement()
    assert st["owner"] == "Alice"
    assert st["balance"] == Decimal("1.00")
    assert st["transactions"] == ["+1.00 RUB"]
    st["transactions"].append("HACK")
    # внутренний список не должен измениться
    assert acc.transactions == ["+1.00 RUB"]


def test_transfer_validates_target_and_amount():
    acc1 = BankAccount("A", 100, "RUB")
    with pytest.raises(TypeError):
        acc1.transfer(None, 10)
    acc2 = BankAccount("B", 0, "RUB")
    with pytest.raises(ValueError):
        acc1.transfer(acc2, 0)
    with pytest.raises(ValueError):
        acc1.transfer(acc2, -1)


def test_transfer_is_atomic_when_conversion_fails():
    acc1 = BankAccount("A", 100, "RUB")
    acc2 = BankAccount("B", 0, "USD")

    class BadConv(CurrencyConverter):
        def convert(self, amount, from_currency, to_currency):
            raise ValueError("no rates")

    with pytest.raises(ValueError):
        acc1.transfer(acc2, 10, converter=BadConv())

    assert acc1.balance == Decimal("100.00")
    assert acc2.balance == Decimal("0.00")


def test_transfer_success_different_currency_real_rates():
    conv = CurrencyConverter({("RUB", "USD"): Decimal("0.01")})
    acc1 = BankAccount("A", 100, "RUB")
    acc2 = BankAccount("B", 0, "USD")
    credited = acc1.transfer(acc2, 10, converter=conv)
    assert credited == Decimal("0.10")
    assert acc1.balance == Decimal("90.00")
    assert acc2.balance == Decimal("0.10")
    assert "Transfer -10.00 RUB" in acc1.transactions[-1]
    assert "Transfer +0.10 USD" in acc2.transactions[-1]


def test_transfer_sender_blocked():
    acc1 = BankAccount("A", 100, "RUB")
    acc2 = BankAccount("B", 0, "RUB")
    acc1.is_blocked = True
    with pytest.raises(PermissionError):
        acc1.transfer(acc2, 1)


def test_bank_create_account_unique_owner():
    bank = Bank("MyBank")
    bank.create_account("Alice", 0, "RUB")
    with pytest.raises(ValueError):
        bank.create_account("Alice", 0, "RUB")


def test_total_deposits_skips_blocked_and_converts():
    conv = CurrencyConverter({("USD", "RUB"): Decimal("100")})
    bank = Bank("MyBank")
    a = bank.create_account("A", 10, "RUB")
    b = bank.create_account("B", 5, "USD")
    b.is_blocked = True
    total = bank.total_deposits("RUB", converter=conv)
    assert total == Decimal("10.00")
