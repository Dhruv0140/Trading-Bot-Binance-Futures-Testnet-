"""Input validation helpers."""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Optional

from .exceptions import ValidationError


VALID_SIDES = {"BUY", "SELL"}
VALID_ORDER_TYPES = {"MARKET", "LIMIT", "STOP_LIMIT"}


def normalize_symbol(symbol: str) -> str:
    value = symbol.strip().upper()
    if not value:
        raise ValidationError("symbol is required")
    if not value.endswith("USDT"):
        raise ValidationError("symbol must be a USDT-M futures symbol, for example BTCUSDT")
    if not value.replace("USDT", "").isalnum():
        raise ValidationError("symbol contains invalid characters")
    return value


def normalize_side(side: str) -> str:
    value = side.strip().upper()
    if value not in VALID_SIDES:
        raise ValidationError("side must be BUY or SELL")
    return value


def normalize_order_type(order_type: str) -> str:
    value = order_type.strip().upper().replace("-", "_")
    if value not in VALID_ORDER_TYPES:
        raise ValidationError("order type must be MARKET, LIMIT, or STOP_LIMIT")
    return value


def positive_decimal(value: str, field_name: str) -> Decimal:
    try:
        parsed = Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise ValidationError(f"{field_name} must be a valid decimal number") from exc

    if parsed <= 0:
        raise ValidationError(f"{field_name} must be greater than zero")
    return parsed


def optional_positive_decimal(value: Optional[str], field_name: str) -> Optional[Decimal]:
    if value is None:
        return None
    return positive_decimal(value, field_name)


def validate_order_input(
    symbol: str,
    side: str,
    order_type: str,
    quantity: str,
    price: Optional[str] = None,
    stop_price: Optional[str] = None,
) -> dict:
    normalized_type = normalize_order_type(order_type)
    normalized_price = optional_positive_decimal(price, "price")
    normalized_stop_price = optional_positive_decimal(stop_price, "stop_price")

    if normalized_type in {"LIMIT", "STOP_LIMIT"} and normalized_price is None:
        raise ValidationError("price is required for LIMIT and STOP_LIMIT orders")
    if normalized_type == "MARKET" and normalized_price is not None:
        raise ValidationError("price is not used for MARKET orders")
    if normalized_type == "STOP_LIMIT" and normalized_stop_price is None:
        raise ValidationError("stop_price is required for STOP_LIMIT orders")
    if normalized_type != "STOP_LIMIT" and normalized_stop_price is not None:
        raise ValidationError("stop_price is only used for STOP_LIMIT orders")

    return {
        "symbol": normalize_symbol(symbol),
        "side": normalize_side(side),
        "order_type": normalized_type,
        "quantity": positive_decimal(quantity, "quantity"),
        "price": normalized_price,
        "stop_price": normalized_stop_price,
    }
