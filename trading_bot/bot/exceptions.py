"""Custom exceptions for the trading bot."""

from typing import Optional


class TradingBotError(Exception):
    """Base exception for application-level trading bot errors."""


class ValidationError(TradingBotError):
    """Raised when user input is invalid."""


class BinanceAPIError(TradingBotError):
    """Raised when Binance returns an API error response."""

    def __init__(self, message: str, status_code: Optional[int] = None, payload: Optional[dict] = None):
        super().__init__(message)
        self.status_code = status_code
        self.payload = payload or {}


class BinanceNetworkError(TradingBotError):
    """Raised when the Binance API cannot be reached."""
