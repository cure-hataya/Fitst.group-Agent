import math
from datetime import date


def validate_expense(item, money):
    """校验消费项目和金额。"""
    if not isinstance(item, str) or not item.strip():
        return "消费项目不能为空"

    if type(money) not in (int, float):
        return "消费金额必须为数字"

    if not math.isfinite(money):
        return "消费金额必须为有限数值"

    if money <= 0:
        return "消费金额必须大于0"

    return None


def validate_expense_date(expense_date):
    """校验消费日期，允许 date 对象或 ISO 格式日期字符串。"""
    if expense_date is None:
        return "消费日期不能为空"

    if isinstance(expense_date, str):
        try:
            expense_date = date.fromisoformat(expense_date)
        except ValueError:
            return "消费日期格式错误"

    if type(expense_date) is not date:
        return "消费日期格式错误"

    if expense_date > date.today():
        return "消费日期不能晚于今天"

    return None


if __name__ == "__main__":
    from datetime import timedelta

    print("===== 消费金额校验 =====")
    print("正常消费：", validate_expense("午餐", 25))
    print("零元消费：", validate_expense("午餐", 0))
    print("负数金额：", validate_expense("午餐", -50))
    print("空白项目：", validate_expense("", 25))
    print("空白金额：", validate_expense("午餐", None))
    print("文字金额：", validate_expense("午餐", "25元"))
    print("无穷金额：", validate_expense("午餐", float("inf")))
    print("异常数值：", validate_expense("午餐", float("nan")))

    print("\n===== 日期校验测试 =====")
    print("今天：", validate_expense_date(date.today()))
    print("昨天：", validate_expense_date(date.today() - timedelta(days=1)))
    print("明天：", validate_expense_date(date.today() + timedelta(days=1)))
    print("错误日期：", validate_expense_date("2026-02-30"))
    print("空白日期：", validate_expense_date(None))
