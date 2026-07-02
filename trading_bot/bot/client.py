"""Small signed REST client for Binance USDT-M Futures Testnet."""

from __future__ import annotations

import hashlib
import hmac
import logging
import time
from decimal import Decimal
from typing import Any
from urllib.parse import urlencode

import requests

from .exceptions import BinanceAPIError, BinanceNetworkError


DEFAULT_BASE_URL = "https://testnet.binancefuture.com"
logger = logging.getLogger(__name__)


class BinanceFuturesClient:
    """Wrapper around the small subset of Binance Futures API used by the bot."""

    def __init__(
        self,
        api_key: str,
        api_secret: str,
        base_url: str = DEFAULT_BASE_URL,
        timeout: int = 10,
        recv_window: int = 5000,
    ):
        self.api_key = api_key
        self.api_secret = api_secret.encode("utf-8")
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.recv_window = recv_window
        self.session = requests.Session()
        self.session.headers.update({"X-MBX-APIKEY": self.api_key})

    def create_order(self, order_params: dict[str, Any]) -> dict[str, Any]:
        return self._signed_request("POST", "/fapi/v1/order", order_params)

    def _signed_request(self, method: str, path: str, params: dict[str, Any]) -> dict[str, Any]:
        request_params = self._prepare_params(params)
        query_string = urlencode(request_params, doseq=True)
        signature = hmac.new(self.api_secret, query_string.encode("utf-8"), hashlib.sha256).hexdigest()
        signed_params = {**request_params, "signature": signature}
        url = f"{self.base_url}{path}"

        logged_params = {key: value for key, value in request_params.items() if key != "signature"}
        logger.info(
            "Sending Binance API request",
            extra={"event": "api_request", "method": method, "url": url, "params": logged_params},
        )

        try:
            response = self.session.request(method, url, params=signed_params, timeout=self.timeout)
        except requests.RequestException as exc:
            logger.error("Network failure while calling Binance API", extra={"event": "api_error", "error": str(exc)})
            raise BinanceNetworkError(f"Network error while calling Binance API: {exc}") from exc

        try:
            payload = response.json()
        except ValueError:
            payload = {"raw": response.text}

        logger.info(
            "Received Binance API response",
            extra={
                "event": "api_response",
                "method": method,
                "url": url,
                "status_code": response.status_code,
                "response": payload,
            },
        )

        if response.status_code >= 400:
            message = payload.get("msg", response.text) if isinstance(payload, dict) else response.text
            raise BinanceAPIError(f"Binance API error: {message}", response.status_code, payload if isinstance(payload, dict) else {})

        return payload if isinstance(payload, dict) else {"response": payload}

    def _prepare_params(self, params: dict[str, Any]) -> dict[str, Any]:
        prepared: dict[str, Any] = {}
        for key, value in params.items():
            if value is None:
                continue
            if isinstance(value, Decimal):
                prepared[key] = format(value, "f")
            else:
                prepared[key] = value
        prepared["recvWindow"] = self.recv_window
        prepared["timestamp"] = int(time.time() * 1000)
        return prepared

