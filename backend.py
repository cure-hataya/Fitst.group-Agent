"""Optional backend adapter for the NiceGUI workbench.

Default mode uses local demo data and does not send any HTTP requests.

To connect a real backend:
1. Replace every "****" in the basic configuration below.
2. Adapt the REQUEST FORMAT functions if your field names differ.
3. Adapt the RESPONSE FORMAT parsers to your actual response shape.
4. Set USE_BACKEND_STATS / USE_BACKEND_CHAT to True.
"""

from __future__ import annotations

from datetime import date
from typing import Any

import httpx

# ---------------------------------------------------------------------------
# Basic configuration
# ---------------------------------------------------------------------------
USE_BACKEND_STATS = False
USE_BACKEND_CHAT = False

BASE_URL = "****"
STATS_PATH = "****"
CHAT_PATH = "****"

REQUEST_TIMEOUT = 20.0
CHAT_TIMEOUT = 90.0

# Optional authentication headers.
HEADERS: dict[str, str] = {
    # "Authorization": "Bearer ****",
}


class BackendError(RuntimeError):
    """Raised when the backend is not configured or returns invalid data."""


def _base_url() -> str:
    value = BASE_URL.strip()
    if not value or "****" in value:
        raise BackendError("请先在 backend.py 中填写 BASE_URL（替换 ****）")
    return value.rstrip("/")


def _endpoint(path: str) -> str:
    value = path.strip()
    if not value or "****" in value:
        raise BackendError("请先在 backend.py 中填写接口路径（替换 ****）")
    if not value.startswith("/"):
        value = "/" + value
    return _base_url() + value


# ---------------------------------------------------------------------------
# REQUEST FORMAT  ****
# Replace these fields/format with the request format required by your backend.
# ---------------------------------------------------------------------------
def build_stats_params(period: str, anchor: date) -> dict[str, Any]:
    """Query parameters sent to the statistics endpoint."""
    return {
        "period": period,
        "date": anchor.isoformat(),
    }


def build_chat_payload(message: str) -> dict[str, Any]:
    """JSON body sent to the chat endpoint."""
    return {
        "message": message,
    }


# ---------------------------------------------------------------------------
# RESPONSE FORMAT  ****
# Adapt these parsers to the actual response of your backend.
# ---------------------------------------------------------------------------
def parse_stats_response(payload: Any) -> dict[str, Any]:
    """Return the stats object consumed by the UI.

    The UI expects this structure (replace with actual backend field names here):

    {
        "range_label": "2026年11月",
        "total": 7139.0,
        "count": 54,
        "average": 339.95,
        "change_direction": "up" | "down" | "flat" | "none",
        "change_pct": 12.3,
        "previous_period_label": "上月",
        "top_category": {
            "label": "购物",
            "color": "#D46484",
            "amount": 4897.0,
            "share": 68.6
        },
        "categories": [
            {"label": "交通", "color": "#5576D9", "amount": 362.0, "share": 5.1},
            ...
        ],
        "trend_labels": ["1日", "2日", ...],
        "trend": [620.0, 842.0, ...],
        "previous_trend": [280.0, 203.0, ...]
    }
    """
    data = payload.get("data", payload) if isinstance(payload, dict) else payload
    if not isinstance(data, dict):
        raise BackendError("统计接口返回格式不正确：应为对象")

    data = dict(data)
    data.setdefault("change_direction", "none")
    data.setdefault("change_pct", None)
    data.setdefault("previous_period_label", "上期")
    data.setdefault("top_category", None)

    required = ("range_label", "total", "count", "average", "categories", "trend_labels", "trend", "previous_trend")
    missing = [key for key in required if key not in data]
    if missing:
        raise BackendError("统计接口缺少字段：" + "、".join(missing))
    return data


def parse_chat_response(payload: Any) -> str:
    """Extract the assistant reply from the backend response."""
    if isinstance(payload, str):
        return payload
    data = payload.get("data", payload) if isinstance(payload, dict) else payload
    if isinstance(data, str):
        return data
    if isinstance(data, dict):
        for key in ("reply", "message", "content", "text"):
            value = data.get(key)
            if isinstance(value, str) and value.strip():
                return value
    raise BackendError("聊天接口返回格式不正确：未找到回复文本")


# ---------------------------------------------------------------------------
# HTTP requests
# ---------------------------------------------------------------------------
async def fetch_stats(period: str, anchor: date) -> dict[str, Any]:
    if not USE_BACKEND_STATS:
        raise BackendError("统计后端尚未启用")
    try:
        async with httpx.AsyncClient(
            timeout=REQUEST_TIMEOUT,
            headers=HEADERS or None,
        ) as client:
            response = await client.get(
                _endpoint(STATS_PATH),
                params=build_stats_params(period, anchor),
            )
            response.raise_for_status()
            try:
                payload = response.json()
            except ValueError as exc:
                raise BackendError("统计接口没有返回有效 JSON") from exc
            return parse_stats_response(payload)
    except BackendError:
        raise
    except httpx.HTTPError as exc:
        raise BackendError(f"统计接口请求失败：{exc}") from exc


async def send_chat(message: str) -> str:
    if not USE_BACKEND_CHAT:
        raise BackendError("聊天后端尚未启用")
    try:
        async with httpx.AsyncClient(
            timeout=CHAT_TIMEOUT,
            headers=HEADERS or None,
        ) as client:
            response = await client.post(
                _endpoint(CHAT_PATH),
                json=build_chat_payload(message),
            )
            response.raise_for_status()
            try:
                payload = response.json()
            except ValueError as exc:
                raise BackendError("聊天接口没有返回有效 JSON") from exc
            return parse_chat_response(payload)
    except BackendError:
        raise
    except httpx.HTTPError as exc:
        raise BackendError(f"聊天接口请求失败：{exc}") from exc
