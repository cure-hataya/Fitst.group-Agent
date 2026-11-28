
def success_response(message="操作成功", data=None):
    return {
        "success": True,
        "message": message,
        "data": data
    }


def error_response(message="操作失败", data=None):
    return {
        "success": False,
        "message": message,
        "data": data
    }

if __name__ == "__main__":
    print("成功测试：", success_response(
        "记账成功",
        {"item": "午餐", "money": 25}
    ))

    print("失败测试：", error_response(
        "消费金额必须大于0"
    ))

    print("默认测试：", success_response())
