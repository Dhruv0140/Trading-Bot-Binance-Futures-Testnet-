"""Command-line interface for the Binance Futures Testnet trading bot."""

from __future__ import annotations

import argparse
import os
import sys
from typing import Any

from bot.client import BinanceFuturesClient, DEFAULT_BASE_URL
from bot.exceptions import BinanceAPIError, BinanceNetworkError, TradingBotError, ValidationError
from bot.logging_config import LOG_FILE, configure_logging
from bot.orders import build_order_payload, place_order
from bot.validators import validate_order_input


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Place orders on Binance Futures Testnet (USDT-M).")
    parser.add_argument("--symbol", required=True, help="Trading symbol, for example BTCUSDT")
    parser.add_argument("--side", required=True, help="BUY or SELL")
    parser.add_argument("--type", required=True, dest="order_type", help="MARKET, LIMIT, or STOP_LIMIT")
    parser.add_argument("--quantity", required=True, help="Order quantity")
    parser.add_argument("--price", help="Limit price. Required for LIMIT and STOP_LIMIT orders")
    parser.add_argument("--stop-price", help="Trigger price. Required for STOP_LIMIT orders")
    parser.add_argument("--api-key", default=os.getenv("BINANCE_API_KEY"), help="Binance testnet API key")
    parser.add_argument("--api-secret", default=os.getenv("BINANCE_API_SECRET"), help="Binance testnet API secret")
    parser.add_argument("--base-url", default=os.getenv("BINANCE_BASE_URL", DEFAULT_BASE_URL), help="Binance Futures API base URL")
    parser.add_argument("--dry-run", action="store_true", help="Validate and log the order without calling Binance")
    return parser.parse_args()


def summarize_request(payload: dict[str, Any], dry_run: bool) -> None:
    print("\nOrder Request Summary")
    print("---------------------")
    for key in ("symbol", "side", "type", "quantity", "price", "stopPrice", "timeInForce"):
        if key in payload:
            print(f"{key}: {payload[key]}")
    print(f"mode: {'DRY RUN' if dry_run else 'LIVE TESTNET'}")


def summarize_response(response: dict[str, Any]) -> None:
    print("\nOrder Response Details")
    print("----------------------")
    fields = {
        "orderId": response.get("orderId"),
        "status": response.get("status"),
        "executedQty": response.get("executedQty"),
        "avgPrice": response.get("avgPrice") or response.get("fills", [{}])[0].get("price") if response.get("fills") else response.get("avgPrice"),
    }
    for key, value in fields.items():
        print(f"{key}: {value if value is not None else 'N/A'}")


def main() -> int:
    configure_logging()
    args = parse_args()

    try:
        validated = validate_order_input(
            symbol=args.symbol,
            side=args.side,
            order_type=args.order_type,
            quantity=args.quantity,
            price=args.price,
            stop_price=args.stop_price,
        )
        payload = build_order_payload(validated)
        summarize_request(payload, args.dry_run)

        if not args.dry_run and (not args.api_key or not args.api_secret):
            raise ValidationError("BINANCE_API_KEY and BINANCE_API_SECRET are required unless --dry-run is used")

        client = BinanceFuturesClient(args.api_key or "", args.api_secret or "", args.base_url)
        response = place_order(client, validated, dry_run=args.dry_run)
        summarize_response(response)

        print(f"\nSuccess: order {'validated' if args.dry_run else 'placed'} successfully.")
        print(f"Log file: {LOG_FILE}")
        return 0

    except ValidationError as exc:
        print(f"\nFailure: invalid input - {exc}", file=sys.stderr)
        return 2
    except BinanceAPIError as exc:
        print(f"\nFailure: Binance API error - {exc}", file=sys.stderr)
        return 1
    except BinanceNetworkError as exc:
        print(f"\nFailure: network error - {exc}", file=sys.stderr)
        return 1
    except TradingBotError as exc:
        print(f"\nFailure: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"\nFailure: unexpected error - {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

