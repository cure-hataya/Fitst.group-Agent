"""Deterministic demo ledger and period statistics for the workbench.

This module contains data only. All UI code is in app.py.
"""

from __future__ import annotations

import calendar
import random
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Any

CATEGORIES: dict[str, dict[str, str]] = {
    "transport": {"label": "交通", "color": "#5576D9"},
    "dining": {"label": "餐饮", "color": "#E78B4B"},
    "shopping": {"label": "购物", "color": "#D46484"},
    "other": {"label": "其他", "color": "#8E88C4"},
}
CATEGORY_KEYS = tuple(CATEGORIES)
WEEKDAYS = ("周一", "周二", "周三", "周四", "周五", "周六", "周日")
NOW = datetime.now()
TODAY = NOW.date()
DATA_START = date(TODAY.year - 1, 1, 1)


@dataclass(frozen=True)
class Expense:
    day: date
    hour: int
    minute: int
    amount: float
    category: str
    note: str


def _triangular(rng: random.Random, low: float, high: float, mode: float) -> float:
    split = (mode - low) / (high - low)
    u = rng.random()
    if u < split:
        return low + (u * (high - low) * (mode - low)) ** 0.5
    return high - ((1 - u) * (high - low) * (high - mode)) ** 0.5


def _build_expenses() -> tuple[Expense, ...]:
    rng = random.Random(18112026)
    notes = {
        "transport": ("地铁通勤", "公交", "打车回家", "停车费", "加了一次油", "高铁票"),
        "dining": ("午餐", "晚餐", "咖啡", "奶茶", "外卖", "和朋友聚餐", "早餐", "水果"),
        "shopping": ("日用品", "新衣服", "超市采购", "家居小物", "护肤品", "周末逛街"),
        "other": ("电影票", "水电费", "一次理发", "视频会员", "买药", "给朋友的礼物"),
    }
    rows: list[Expense] = []
    day = DATA_START
    while day < TODAY:
        weekend = day.weekday() >= 5
        count = rng.choices((1, 2, 3, 4), weights=(0.10, 0.38, 0.36, 0.16), k=1)[0]
        if weekend and rng.random() < 0.34:
            count += 1
        weights = (0.30, 0.38, 0.22, 0.10) if not weekend else (0.22, 0.33, 0.30, 0.15)
        categories = rng.choices(CATEGORY_KEYS, weights=weights, k=count)
        minutes = sorted(rng.randint(7 * 60, 22 * 60) for _ in range(count))
        for minute, category in zip(minutes, categories):
            if category == "dining":
                amount = int(_triangular(rng, 12, 128, 34))
            elif category == "transport":
                amount = int(_triangular(rng, 4, 86, 18))
            elif category == "shopping":
                amount = int(_triangular(rng, 25, 680, 116))
            else:
                amount = int(_triangular(rng, 8, 420, 58))
            rows.append(
                Expense(
                    day=day,
                    hour=minute // 60,
                    minute=minute % 60,
                    amount=float(max(1, amount)),
                    category=category,
                    note=rng.choice(notes[category]),
                )
            )
        day += timedelta(days=1)

    # Keep today's demo easy to understand and fully in the past.
    rows.append(Expense(TODAY, 9, 30, 36.0, "dining", "早餐和咖啡"))
    rows.append(Expense(TODAY, 12, 20, 22.0, "transport", "打车回家"))
    return tuple(rows)


EXPENSES = _build_expenses()


def period_bounds(anchor: date, period: str) -> tuple[date, date]:
    """Return the inclusive start and exclusive end of a calendar period."""
    if period == "day":
        return anchor, anchor + timedelta(days=1)
    if period == "week":
        start = anchor - timedelta(days=anchor.weekday())
        return start, start + timedelta(days=7)
    if period == "month":
        start = anchor.replace(day=1)
        if start.month == 12:
            end = date(start.year + 1, 1, 1)
        else:
            end = date(start.year, start.month + 1, 1)
        return start, end
    if period == "year":
        return date(anchor.year, 1, 1), date(anchor.year + 1, 1, 1)
    raise ValueError(f"未知统计周期: {period}")


def previous_bounds(anchor: date, period: str) -> tuple[date, date]:
    start, end = period_bounds(anchor, period)
    if period == "day":
        return start - timedelta(days=1), start
    if period == "week":
        return start - timedelta(days=7), start
    if period == "month":
        return (
            date(start.year, start.month - 1, 1)
            if start.month > 1
            else date(start.year - 1, 12, 1),
            start,
        )
    return date(start.year - 1, 1, 1), date(start.year, 1, 1)


def shift_anchor(anchor: date, period: str, direction: int) -> date:
    if period == "day":
        return anchor + timedelta(days=direction)
    if period == "week":
        return anchor + timedelta(days=7 * direction)
    if period == "month":
        month_index = anchor.year * 12 + anchor.month - 1 + direction
        year, month = divmod(month_index, 12)
        last_day = calendar.monthrange(year, month + 1)[1]
        return date(year, month + 1, min(anchor.day, last_day))
    if period == "year":
        return date(anchor.year + direction, anchor.month, min(anchor.day, 28))
    raise ValueError(f"未知统计周期: {period}")


def _rows_between(start: date, end: date) -> list[Expense]:
    return [expense for expense in EXPENSES if start <= expense.day < end]


def _bucket_labels(period: str, start: date) -> list[str]:
    if period == "day":
        return [f"{hour:02d}时" for hour in range(0, 24, 3)]
    if period == "week":
        return list(WEEKDAYS)
    if period == "month":
        days = calendar.monthrange(start.year, start.month)[1]
        return [f"{day}日" for day in range(1, days + 1)]
    return [f"{month}月" for month in range(1, 13)]


def _bucket_amounts(period: str, start: date, rows: list[Expense]) -> list[float]:
    length = len(_bucket_labels(period, start))
    values = [0.0] * length
    if period == "day":
        for expense in rows:
            values[min(7, expense.hour // 3)] += expense.amount
    elif period == "week":
        for expense in rows:
            index = (expense.day - start).days
            if 0 <= index < 7:
                values[index] += expense.amount
    elif period == "month":
        for expense in rows:
            index = expense.day.day - 1
            if 0 <= index < length:
                values[index] += expense.amount
    else:
        for expense in rows:
            values[expense.day.month - 1] += expense.amount
    return [round(value, 2) for value in values]


def _active_days(start: date, end: date) -> int:
    if start > TODAY:
        return 0
    last_seen = min(end - timedelta(days=1), TODAY)
    return max(0, (last_seen - start).days + 1)


def _trend_limit(period: str, start: date, end: date) -> int:
    if not (start <= TODAY < end):
        return len(_bucket_labels(period, start))
    if period == "day":
        return min(8, NOW.hour // 3 + 1)
    if period == "week":
        return (TODAY - start).days + 1
    if period == "month":
        return TODAY.day
    return TODAY.month


def _period_label(period: str, start: date, end: date) -> str:
    last = end - timedelta(days=1)
    if period == "day":
        return f"{start.year}年{start.month}月{start.day}日"
    if period == "week":
        if start.year == last.year:
            return f"{start.year}年{start.month}月{start.day}日 – {last.month}月{last.day}日"
        return f"{start.year}年{start.month}月{start.day}日 – {last.year}年{last.month}月{last.day}日"
    if period == "month":
        return f"{start.year}年{start.month}月"
    return f"{start.year}年"


def get_stats(period: str, anchor: date) -> dict[str, Any]:
    if period not in {"day", "week", "month", "year"}:
        raise ValueError(f"未知统计周期: {period}")
    start, end = period_bounds(anchor, period)
    prev_start, prev_end = previous_bounds(anchor, period)
    rows = _rows_between(start, end)
    prev_rows = _rows_between(prev_start, prev_end)

    total = round(sum(row.amount for row in rows), 2)
    prev_total = round(sum(row.amount for row in prev_rows), 2)
    active_days = _active_days(start, end)
    category_totals = {key: 0.0 for key in CATEGORY_KEYS}
    for row in rows:
        category_totals[row.category] += row.amount

    categories = [
        {
            "key": key,
            "label": CATEGORIES[key]["label"],
            "color": CATEGORIES[key]["color"],
            "amount": round(category_totals[key], 2),
            "share": round(category_totals[key] / total * 100, 1) if total else 0.0,
        }
        for key in CATEGORY_KEYS
    ]
    top = max(categories, key=lambda item: item["amount"])
    top_category = (
        {
            "key": top["key"],
            "label": top["label"],
            "color": top["color"],
            "amount": top["amount"],
            "share": top["share"],
        }
        if total > 0
        else None
    )

    labels = _bucket_labels(period, start)
    limit = _trend_limit(period, start, end)
    labels = labels[:limit]
    trend = _bucket_amounts(period, start, rows)[:limit]
    previous_full = _bucket_amounts(period, prev_start, prev_rows)
    previous_trend = previous_full[:limit]
    if len(previous_trend) < len(trend):
        previous_trend += [0.0] * (len(trend) - len(previous_trend))

    change_pct: float | None = None
    change_direction = "none"
    if prev_total > 0:
        change = (total - prev_total) / prev_total * 100
        change_pct = round(change, 1)
        if abs(change) < 0.05:
            change_direction = "flat"
        else:
            change_direction = "up" if change > 0 else "down"

    previous_names = {"day": "前一日", "week": "上周", "month": "上月", "year": "去年"}
    return {
        "period": period,
        "anchor": anchor,
        "start": start,
        "end": end,
        "range_label": _period_label(period, start, end),
        "total": total,
        "count": len(rows),
        "active_days": active_days,
        "average": round(total / active_days, 2) if active_days else 0.0,
        "previous_total": prev_total,
        "change_pct": change_pct,
        "change_direction": change_direction,
        "previous_period_label": previous_names[period],
        "top_category": top_category,
        "categories": categories,
        "trend_labels": labels,
        "trend": trend,
        "previous_trend": previous_trend,
        "has_data": bool(rows),
    }


def can_go_forward(anchor: date, period: str) -> bool:
    _, end = period_bounds(anchor, period)
    return end <= TODAY
