"""Pure-Python NiceGUI workbench.

Run:
    python app.py

The interface, demo data and all interactions use Python. NiceGUI handles the
browser rendering; there is no separate HTML/CSS/JavaScript frontend.
"""

from __future__ import annotations

import argparse
from datetime import date
from typing import Any

try:
    from nicegui import ui
except ModuleNotFoundError:
    raise SystemExit("缺少依赖：请先运行 python -m pip install -r requirements.txt") from None

import demo_data
import backend
from demo_data import CATEGORIES, TODAY, can_go_forward, get_stats, shift_anchor

PAGE_BG = "#f5f2eb"
SURFACE = "#fffdf9"
SIDEBAR_BG = "#1d302a"
INK = "#202d27"
MUTED = "#858a82"
LINE = "#e7e0d5"
ACCENT = "#d96747"
GREEN = "#4e7662"
FONT = "'Microsoft YaHei', 'PingFang SC', 'Segoe UI', sans-serif"


def money(value: float, decimals: int = 2) -> str:
    return f"¥{value:,.{decimals}f}"


def compact_money(value: float) -> str:
    if value >= 10000:
        return f"¥{value / 10000:.1f}万".replace(".0万", "万")
    return f"¥{value:,.0f}"


def short_change(data: dict[str, Any]) -> str:
    if data["change_direction"] == "none":
        return "暂无对比"
    if data["change_direction"] == "flat":
        return f"与{data['previous_period_label']}持平"
    arrow = "↑" if data["change_direction"] == "up" else "↓"
    return f"较{data['previous_period_label']} {arrow} {abs(data['change_pct']):.1f}%"


def change_color(direction: str) -> str:
    if direction == "up":
        return "#a3593f"
    if direction == "down":
        return GREEN
    return MUTED


def bar_options(data: dict[str, Any]) -> dict[str, Any]:
    categories = data["categories"]
    return {
        "animationDuration": 350,
        "textStyle": {"fontFamily": FONT},
        "grid": {"left": 18, "right": 18, "top": 38, "bottom": 40, "containLabel": True},
        "tooltip": {
            "trigger": "axis",
            "axisPointer": {"type": "shadow"},
            "backgroundColor": "rgba(31,45,38,.94)",
            "borderWidth": 0,
            "textStyle": {"color": "#fbf5e9", "fontSize": 12},
        },
        "xAxis": {
            "type": "category",
            "data": [item["label"] for item in categories],
            "axisTick": {"show": False},
            "axisLine": {"lineStyle": {"color": "#ddd6ca"}},
            "axisLabel": {
                "fontSize": 14,
                "fontWeight": 600,
                "color": "#2f3c34",
                "margin": 14,
            },
        },
        "yAxis": {
            "type": "value",
            "splitLine": {"lineStyle": {"color": "#eee8de", "type": [2, 4]}},
            "axisLabel": {"fontSize": 11, "color": MUTED, "formatter": "¥{value}"},
        },
        "series": [
            {
                "type": "bar",
                "barWidth": 48,
                "data": [
                    {
                        "value": item["amount"],
                        "itemStyle": {
                            "color": item["color"],
                            "borderRadius": [8, 8, 2, 2],
                        },
                    }
                    for item in categories
                ],
                "label": {
                    "show": True,
                    "position": "top",
                    "formatter": "¥{c}",
                    "fontSize": 11,
                    "color": "#5d675f",
                },
            }
        ],
    }


def pie_options(data: dict[str, Any]) -> dict[str, Any]:
    active = [item for item in data["categories"] if item["amount"] > 0]
    return {
        "animationDuration": 350,
        "textStyle": {"fontFamily": FONT},
        "tooltip": {
            "trigger": "item",
            "formatter": "{b}: ¥{c} ({d}%)",
            "backgroundColor": "rgba(31,45,38,.94)",
            "borderWidth": 0,
            "textStyle": {"color": "#fbf5e9", "fontSize": 12},
        },
        "series": [
            {
                "type": "pie",
                "radius": ["34%", "56%"],
                "center": ["50%", "50%"],
                "avoidLabelOverlap": True,
                "percentPrecision": 1,
                "label": {
                    "show": True,
                    "position": "outside",
                    "formatter": "{b}\n{d}%",
                    "fontSize": 13,
                    "fontWeight": 600,
                    "color": "#3b463f",
                    "lineHeight": 19,
                },
                "labelLine": {
                    "length": 10,
                    "length2": 8,
                    "lineStyle": {"color": "#c9c1b4"},
                },
                "itemStyle": {
                    "borderColor": SURFACE,
                    "borderWidth": 3,
                    "borderRadius": 2,
                },
                "data": [
                    {
                        "name": item["label"],
                        "value": item["amount"],
                        "itemStyle": {"color": item["color"]},
                    }
                    for item in active
                ],
            }
        ],
    }


def line_options(data: dict[str, Any]) -> dict[str, Any]:
    return {
        "animationDuration": 350,
        "textStyle": {"fontFamily": FONT},
        "legend": {
            "top": 4,
            "right": 8,
            "itemWidth": 14,
            "itemHeight": 8,
            "textStyle": {"fontSize": 11, "color": MUTED},
            "data": ["本周期", "上周期"],
        },
        "grid": {"left": 18, "right": 18, "top": 46, "bottom": 38, "containLabel": True},
        "tooltip": {
            "trigger": "axis",
            "backgroundColor": "rgba(31,45,38,.94)",
            "borderWidth": 0,
            "textStyle": {"color": "#fbf5e9", "fontSize": 12},
        },
        "xAxis": {
            "type": "category",
            "data": data["trend_labels"],
            "boundaryGap": False,
            "axisTick": {"show": False},
            "axisLine": {"lineStyle": {"color": "#ddd6ca"}},
            "axisLabel": {"fontSize": 11, "color": MUTED, "margin": 12},
        },
        "yAxis": {
            "type": "value",
            "splitLine": {"lineStyle": {"color": "#eee8de", "type": [2, 4]}},
            "axisLabel": {"fontSize": 11, "color": MUTED, "formatter": "¥{value}"},
        },
        "series": [
            {
                "name": "上周期",
                "type": "line",
                "data": data["previous_trend"],
                "symbol": "none",
                "lineStyle": {"width": 1.4, "type": "dashed", "color": "#b8afa2"},
                "itemStyle": {"color": "#b8afa2"},
            },
            {
                "name": "本周期",
                "type": "line",
                "data": data["trend"],
                "symbol": "circle",
                "symbolSize": 5,
                "showSymbol": len(data["trend"]) <= 20,
                "lineStyle": {"width": 2.2, "color": ACCENT},
                "itemStyle": {"color": ACCENT, "borderColor": SURFACE, "borderWidth": 1},
                "areaStyle": {"color": "rgba(217, 103, 71, 0.10)"},
            },
        ],
    }


def page_title(text: str) -> None:
    ui.label(text).style(
        f"font-size: 1.4rem; font-weight: 600; color: {INK}; letter-spacing: -0.02em; "
        "margin-bottom: 1rem;"
    )


def card_style(extra: str = "") -> str:
    return (
        f"background: {SURFACE}; border: 1px solid {LINE}; border-radius: 16px; "
        "box-shadow: none; overflow: hidden; " + extra
    )


@ui.page("/")
def workbench() -> None:
    ui.colors(primary=SIDEBAR_BG, secondary=ACCENT, accent=ACCENT)
    ui.query("body").style(f"background: {PAGE_BG};")
    ui.query(".nicegui-content").style(
        "padding: 0; max-width: none; width: 100%; height: 100vh; gap: 0;"
    )

    state = {
        "page": "chat",
        "period": "month",
        "anchor": TODAY,
    }
    initial_stats = get_stats(state["period"], state["anchor"])

    nav_buttons: dict[str, ui.button] = {}
    with ui.row(wrap=False, align_items="stretch").classes(
        "w-full h-screen flex-col md:flex-row"
    ).style("gap: 0;"):
        with ui.column().classes("w-full md:w-52 flex-none").style(
            f"background: {SIDEBAR_BG}; color: #f5efe4; padding: 1rem .75rem;"
        ):
            with ui.row(wrap=True).classes("w-full md:flex-col").style("gap: .35rem;"):
                for key, label, icon in (
                    ("chat", "对话", "chat_bubble_outline"),
                    ("analysis", "分析台", "bar_chart"),
                ):
                    button = ui.button(
                        label,
                        icon=icon,
                        on_click=lambda _=None, page=key: show_page(page),
                    ).props("flat no-caps align=left color=white").classes(
                        "w-auto md:w-full"
                    ).style(
                        "justify-content: flex-start; border-radius: 9px; padding: .6rem .75rem;"
                    )
                    nav_buttons[key] = button

        with ui.column().classes("flex-1 w-full min-h-0 overflow-y-auto p-4 md:p-8").style(
            f"background: {PAGE_BG};"
        ):
            root = ui.column().style("width: 100%; max-width: 1180px; margin: 0 auto; gap: 1rem;")
            with root:
                chat_page = ui.column().style(
                    "width: 100%; max-width: 960px; margin: 0 auto; gap: 1rem;"
                )
                analysis_page = ui.column().style("width: 100%; gap: 1rem;")
                analysis_page.set_visibility(False)

    # Conversation --------------------------------------------------------
    with chat_page:
        page_title("对话")
        with ui.card().tight().style(
            card_style(
                "width: 100%; "
                "height: calc(100vh - 13rem); min-height: 380px; "
                "display: flex; flex-direction: column;"
            )
        ):
            message_area = ui.column().style(
                "flex: 1; min-height: 0; overflow-y: auto; width: 100%; padding: 1.35rem; gap: .75rem;"
            )
            with ui.row().style(
                f"width: 100%; gap: .5rem; padding: .75rem; border-top: 1px solid {LINE};"
            ):
                chat_input = (
                    ui.input(placeholder="输入消息…")
                    .props("outlined dense")
                    .style("flex: 1;")
                )
                send_button = ui.button(icon="send").props("round unelevated color=primary")

    def append_chat_bubble(text: str, *, sent: bool, error: bool = False) -> None:
        if error:
            background, color, border = "#fbefeb", "#9c5845", "#efd8d0"
        elif sent:
            background, color, border = "#2a463c", "#fbf5e9", "#2a463c"
        else:
            background, color, border = "#f4efe6", "#2d3a33", "#eae2d6"
        radius = "14px 4px 14px 14px" if sent else "4px 14px 14px 14px"
        with message_area:
            with ui.row().style(
                f"width: 100%; justify-content: {'flex-end' if sent else 'flex-start'};"
            ):
                ui.label(text).style(
                    f"background: {background}; color: {color}; border: 1px solid {border}; "
                    f"padding: .65rem .9rem; border-radius: {radius}; max-width: 75%; "
                    "white-space: pre-wrap; overflow-wrap: anywhere; font-size: .9rem; "
                    "line-height: 1.65;"
                )

    chat_busy = False

    async def send_message(_event: Any = None) -> None:
        nonlocal chat_busy
        if chat_busy:
            return
        text = (chat_input.value or "").strip()
        if not text:
            return
        append_chat_bubble(text, sent=True)
        chat_input.value = ""
        chat_input.run_method("focus")
        if not backend.USE_BACKEND_CHAT:
            return

        chat_busy = True
        send_button.set_enabled(False)
        try:
            reply = await backend.send_chat(text)
            append_chat_bubble(reply, sent=False)
        except Exception as exc:
            append_chat_bubble(f"后端请求失败：{exc}", sent=False, error=True)
            ui.notify(f"聊天后端请求失败：{exc}", type="negative")
        finally:
            chat_busy = False
            send_button.set_enabled(True)
            chat_input.run_method("focus")

    chat_input.on("keydown.enter", send_message)
    send_button.on("click", send_message)

    # Analysis ------------------------------------------------------------
    with analysis_page:
        page_title("分析台")

        with ui.row().style(
            "width: 100%; align-items: center; flex-wrap: wrap; gap: .6rem;"
        ):
            period_toggle = ui.toggle(
                {"day": "日", "week": "周", "month": "月", "year": "年"},
                value=state["period"],
            ).props("unelevated no-caps")
            prev_button = ui.button(icon="chevron_left").props("flat round dense")
            date_input = ui.input(value=state["anchor"].isoformat()).props(
                "type=date outlined dense"
            ).style("width: 152px;")
            next_button = ui.button(icon="chevron_right").props("flat round dense")
            today_button = ui.button("今天").props("flat no-caps")
            range_label = ui.label(initial_stats["range_label"]).style(
                f"margin-left: auto; font-size: .76rem; color: {MUTED}; white-space: nowrap;"
            )

        with ui.card().tight().style(card_style("width: 100%; padding: 1.15rem 1.35rem;")):
            with ui.row().style(
                "width: 100%; align-items: center; flex-wrap: wrap; gap: 1.5rem 2.5rem;"
            ):
                with ui.column().style("gap: .15rem; min-width: 175px;"):
                    ui.label("总支出").style(f"font-size: .74rem; color: {MUTED};")
                    total_label = ui.label("—").style(
                        f"font-size: 2rem; font-weight: 600; color: {INK}; letter-spacing: -0.04em;"
                    )
                    change_label = ui.label("—").style(f"font-size: .74rem; color: {MUTED};")
                summary_values: dict[str, ui.label] = {}
                with ui.row().style(
                    "flex: 1 1 420px; min-width: 0; flex-wrap: nowrap; gap: 0;"
                ):
                    for key, label in (
                        ("average", "日均"),
                        ("count", "笔数"),
                        ("top", "主要分类"),
                    ):
                        with ui.column().style(
                            "flex: 1; min-width: 0; gap: .15rem; "
                            "border-left: 1px solid #eee8de; padding-left: 1.25rem;"
                        ):
                            ui.label(label).style(f"font-size: .74rem; color: {MUTED};")
                            summary_values[key] = ui.label("—").style(
                                f"font-size: 1rem; font-weight: 600; color: {INK};"
                            )

        with ui.row().style("width: 100%; gap: 1rem; flex-wrap: wrap; align-items: stretch;"):
            with ui.card().tight().style(card_style("flex: 1 1 360px; min-width: 300px;")):
                ui.label("分类支出").style(
                    f"font-size: 1.05rem; font-weight: 600; color: {INK}; padding: 1rem 1.15rem .25rem;"
                )
                bar_chart = ui.echart(bar_options(initial_stats)).style(
                    "width: 100%; height: 320px;"
                )
            with ui.card().tight().style(card_style("flex: 1 1 360px; min-width: 300px;")):
                ui.label("支出结构").style(
                    f"font-size: 1.05rem; font-weight: 600; color: {INK}; padding: 1rem 1.15rem .25rem;"
                )
                pie_chart = ui.echart(pie_options(initial_stats)).style(
                    "width: 100%; height: 320px;"
                )

        with ui.card().tight().style(card_style("width: 100%; padding-top: .25rem;")):
            ui.label("消费趋势").style(
                f"font-size: 1.05rem; font-weight: 600; color: {INK}; padding: 1rem 1.15rem .25rem;"
            )
            line_chart = ui.echart(line_options(initial_stats)).style(
                "width: 100%; height: 310px;"
            )

        def update_summary(data: dict[str, Any]) -> None:
            total_label.text = money(data["total"])
            change_label.text = short_change(data)
            change_label.style(
                f"font-size: .74rem; color: {change_color(data['change_direction'])}; "
                "font-weight: 500;"
            )
            summary_values["average"].text = money(data["average"])
            summary_values["count"].text = str(data["count"])
            top = data["top_category"]
            summary_values["top"].text = top["label"] if top else "—"
            if top:
                summary_values["top"].style(
                    f"font-size: 1rem; font-weight: 600; color: {top['color']};"
                )
            else:
                summary_values["top"].style(
                    f"font-size: 1rem; font-weight: 600; color: {MUTED};"
                )

        refresh_state = {"seq": 0}

        def apply_stats(data: dict[str, Any]) -> None:
            range_label.text = data["range_label"]
            update_summary(data)
            for chart, options in (
                (bar_chart, bar_options(data)),
                (pie_chart, pie_options(data)),
                (line_chart, line_options(data)),
            ):
                chart.options.clear()
                chart.options.update(options)
                chart.update()

        async def refresh() -> None:
            period = str(period_toggle.value)
            try:
                anchor = date.fromisoformat(str(date_input.value))
            except ValueError:
                anchor = TODAY
                date_input.value = anchor.isoformat()
            if anchor > TODAY:
                anchor = TODAY
                date_input.value = anchor.isoformat()
            next_button.set_enabled(can_go_forward(anchor, period))

            refresh_state["seq"] += 1
            seq = refresh_state["seq"]
            if backend.USE_BACKEND_STATS:
                range_label.text = "正在读取后端…"
                try:
                    data = await backend.fetch_stats(period, anchor)
                except Exception as exc:
                    if seq != refresh_state["seq"]:
                        return
                    range_label.text = "后端读取失败"
                    ui.notify(f"统计数据读取失败：{exc}", type="negative")
                    return
            else:
                data = get_stats(period, anchor)

            if seq != refresh_state["seq"]:
                return
            try:
                apply_stats(data)
            except Exception as exc:
                range_label.text = "数据格式错误"
                ui.notify(f"统计数据格式不正确：{exc}", type="negative")

        async def change_date(event: Any) -> None:
            raw = str(event.value or "").strip()
            if not raw:
                date_input.value = TODAY.isoformat()
            await refresh()

        async def step(direction: int) -> None:
            period = str(period_toggle.value)
            anchor = date.fromisoformat(str(date_input.value))
            new_anchor = shift_anchor(anchor, period, direction)
            if new_anchor > TODAY:
                new_anchor = TODAY
            date_input.value = new_anchor.isoformat()
            await refresh()

        async def go_prev(_event: Any = None) -> None:
            await step(-1)

        async def go_next(_event: Any = None) -> None:
            await step(1)

        async def go_today(_event: Any = None) -> None:
            date_input.value = TODAY.isoformat()
            await refresh()

        async def change_period(_event: Any = None) -> None:
            await refresh()

        period_toggle.on_value_change(change_period)
        date_input.on_value_change(change_date)
        prev_button.on("click", go_prev)
        next_button.on("click", go_next)
        today_button.on("click", go_today)
        next_button.set_enabled(can_go_forward(state["anchor"], state["period"]))
        update_summary(initial_stats)
        if backend.USE_BACKEND_STATS:
            ui.timer(0.2, refresh, once=True)

    # Page switching ------------------------------------------------------
    def show_page(page: str) -> None:
        state["page"] = page
        chat_page.set_visibility(page == "chat")
        analysis_page.set_visibility(page == "analysis")
        for key, button in nav_buttons.items():
            active = key == page
            button.style(
                "justify-content: flex-start; border-radius: 9px; padding: .6rem .75rem; "
                + (
                    "background: rgba(255,255,255,.12); opacity: 1;"
                    if active
                    else "background: transparent; opacity: .62;"
                )
            )

    show_page("chat")


def main() -> None:
    parser = argparse.ArgumentParser(description="个人记账工作台 · NiceGUI")
    parser.add_argument("--host", default="127.0.0.1", help="监听地址，默认 127.0.0.1")
    parser.add_argument("--port", type=int, default=8080, help="监听端口，默认 8080")
    parser.add_argument("--no-open", action="store_true", help="启动时不自动打开浏览器")
    args, _ = parser.parse_known_args()
    ui.run(
        host=args.host,
        port=args.port,
        title="记账工作台",
        language="zh-CN",
        favicon="📊",
        reload=False,
        show=not args.no_open,
        show_welcome_message=False,
    )


if __name__ in {"__main__", "__mp_main__"}:
    main()
