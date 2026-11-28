
def find_duplicate(records, item, money, expense_date):
    for record in records:
        if (
            record["item"].strip() == item.strip()
            and record["money"] == money
            and str(record.get("date")) == str(expense_date)
        ):
            return record

    return None

if __name__ == "__main__":
    records = [
        {
            "id": 1,
            "item": "午餐",
            "money": 25,
            "category": "餐饮",
            "date": "2026-11-28"
        }
    ]

    print("重复账单：", find_duplicate(
        records, "午餐", 25, "2026-11-28"
    ))

    print("不同金额：", find_duplicate(
        records, "午餐", 50, "2026-11-28"
    ))

    print("不同日期：", find_duplicate(
        records, "午餐", 25, "2026-11-27"
    ))

    print("不同项目：", find_duplicate(
        records, "晚餐", 25, "2026-11-28"
    ))
