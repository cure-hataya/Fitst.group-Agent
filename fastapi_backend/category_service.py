
STANDARD_CATEGORIES = (
    "餐饮",
    "交通",
    "购物",
    "娱乐",
    "学习",
    "医疗",
    "生活",
    "其他"
)

CATEGORY_ALIASES = {
    "美食": "餐饮",
    "饮食": "餐饮",
    "食品": "餐饮",
    "出行": "交通",
    "交通费": "交通",
    "服饰": "购物",
    "网购": "购物",
    "休闲": "娱乐",
    "文娱": "娱乐",
    "教育": "学习",
    "书籍": "学习",
    "医药": "医疗",
    "健康": "医疗",
    "日用品": "生活",
    "生活用品": "生活"
}


def normalize_category(category):
    if not isinstance(category, str):
        return "其他"

    category = category.strip()

    if category in STANDARD_CATEGORIES:
        return category

    return CATEGORY_ALIASES.get(category, "其他")

if __name__ == "__main__":
    print("美食：", normalize_category("美食"))
    print("出行：", normalize_category("出行"))
    print("网购：", normalize_category("网购"))
    print("教育：", normalize_category("教育"))
    print("医药：", normalize_category("医药"))
    print("餐饮：", normalize_category("餐饮"))
    print("未知类别：", normalize_category("未知类别"))
    print("空值：", normalize_category(None))
