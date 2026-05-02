"""AWS Lambda entrypoint for journalist-helper."""

from __future__ import annotations

import logging

import main as app_main

logger = logging.getLogger(__name__)


def lambda_handler(_event: dict[str, object], _context: object) -> dict[str, object]:
    """Invoke the existing app flow and return a compact Lambda response."""
    logger.info("Lambda invocation started")

    result = app_main.main()

    preview = (result or "")[:500]
    return {
        "statusCode": 200,
        "ok": True,
        "resultPreview": preview,
        "resultLength": len(result or ""),
    }
