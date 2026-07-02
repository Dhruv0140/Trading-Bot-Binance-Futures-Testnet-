"""Order placement logic."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from .client import BinanceFuturesClient


logger = logging.getLogger(__name__)


def build_order_payload(validated: dict[str, Any]) -> dict[str, Any]:
    order_type = validated["order_type"]
    api_type = "STOP" if order_type == "STOP_LIMIT" else order_type

    payload = {
        "symbol": validated["symbol"],
        "side": validated["side"],
        "type": api_type,
        "quantity": validated["quantity"],
    }

    if order_type in {"LIMIT", "STOP_LIMIT"}:
        payload["price"] = validated["price"]
        payload["timeInForce"] = "GTC"

    if order_type == "STOP_LIMIT":
        payload["stopPrice"] = validated["stop_price"]

    return payload


def place_order(client: BinanceFuturesClient, validated: dict[str, Any], dry_run: bool = False) -> dict[str, Any]:
    payload = build_order_payload(validated)
    logger.info("Prepared order payload", extra={"event": "order_request", "params": payload})

    if dry_run:
        response = {
            "dryRun": True,
            "orderId": "DRY-RUN",
            "status": "SIMULATED",
            "executedQty": "0",
            "avgPrice": "0",
            "transactTime": datetime.now(timezone.utc).isoformat(),
            "request": {key: str(value) for key, value in payload.items()},
        }
        logger.info("Dry-run order response", extra={"event": "order_response", "response": response})
        return response

    response = client.create_order(payload)
    logger.info("Order placed successfully", extra={"event": "order_response", "response": response})
    return response

