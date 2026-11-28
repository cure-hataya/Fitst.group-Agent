from datetime import date
import json
import os
from pathlib import Path
from dotenv import load_dotenv

from openai import (
    OpenAI,
    APITimeoutError,
    APIConnectionError,
    AuthenticationError,
    RateLimitError,
    APIStatusError
)


load_dotenv(Path(__file__).with_name(".env"))



def ask_llm(text, system_prompt=None):


    client = OpenAI(
        api_key=os.getenv("DASHSCOPE_API_KEY"),
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        timeout=30.0,
        max_retries=1
    )


    response = client.chat.completions.create(
        model="qwen-plus",
        messages=[
            {
                "role": "system",



"content": system_prompt or f"""

你是一个消费账单解析助手。
当前日期为：{date.today().isoformat()}。

请从用户输入中提取以下信息：
1. item：消费项目
2. money：消费金额，必须为数字

3. category：消费类别
   只能从以下八种类别中选择：
   餐饮、交通、购物、娱乐、学习、医疗、生活、其他。
   不允许自行创造新的类别名称。
   无法判断消费类别时归入其他。

4. date：消费日期，格式为YYYY-MM-DD

根据当前日期解析昨天、前天等时间表达。
如果无法确定消费日期，则返回null。
缺失的信息返回null，不要编造数据。
只返回JSON格式的数据，不要输出额外解释。
"""


            },
            {
                "role": "user",
                "content": text
            }
        ],

        response_format={"type": "json_object"},
        extra_body={"enable_thinking": False}

    )


    content = response.choices[0].message.content

    return json.loads(content)




def validate_bill(data):
    import math

    if not isinstance(data, dict):
        return "账单数据格式错误"

    item = data.get("item")
    money = data.get("money")
    category = data.get("category")
    expense_date = data.get("date")

    if not isinstance(item, str) or not item.strip():
        return "缺少消费项目"

    if type(money) not in (int, float):
        return "消费金额缺失或格式错误"

    if not math.isfinite(money) or money <= 0:
        return "消费金额必须为有效的正数"

    if not isinstance(category, str) or not category.strip():
        return "缺少消费类别"

    if not expense_date:
        return "缺少消费日期"

    try:
        date.fromisoformat(expense_date)
    except (ValueError, TypeError):
        return "消费日期格式错误"

    return None



def parse_bill(text):
    bill = ask_llm(text)

    error = validate_bill(bill)

    if error is not None:
        return {
            "success": False,
            "message": error,
            "bill": bill
        }

    return {
        "success": True,
        "message": "账单解析成功",
        "bill": bill
    }

def parse_query(text):
    prompt = f"""
你是一个智能消费查询助手。
当前日期为：{date.today().isoformat()}。

请根据用户的问题提取以下信息：

1. start_date：查询开始日期
2. end_date：查询结束日期

3. category：消费类别
   只能从以下八种类别中选择：
   餐饮、交通、购物、娱乐、学习、医疗、生活、其他。
   查询全部类别时返回null。
   将美食、饮食统一为餐饮。
   将出行、交通费统一为交通。
   不允许自行创造新的类别。

4. metric：统计方式

统计方式只能是：
total：消费总金额
count：消费笔数
average：平均每笔消费金额
top_category：消费金额最高的类别

日期格式必须为YYYY-MM-DD。
正确理解今天、昨天、本周、本月、上个月等时间表达。
如果没有指定时间范围，日期返回null。
如果无法判断统计方式，返回null。
不要编造消费数据。
只返回JSON格式，不要输出额外解释。
"""

    return ask_llm(text, system_prompt=prompt)


def validate_query(data):
    if not isinstance(data, dict):
        return "查询数据格式错误"

    metric = data.get("metric")
    category = data.get("category")
    start = data.get("start_date")
    end = data.get("end_date")

    if metric not in (
        "total", "count", "average", "top_category"
    ):
        return "无法确定统计方式"

    if category is not None:
        if not isinstance(category, str) or not category.strip():
            return "消费类别格式错误"

    if metric == "top_category" and category is not None:
        return "类别排名需要查询全部类别"

    if start is None and end is None:
        return None

    if start is None or end is None:
        return "查询时间范围不完整"

    try:
        start_date = date.fromisoformat(start)
        end_date = date.fromisoformat(end)
    except (ValueError, TypeError):
        return "查询日期格式错误"

    if start_date > end_date:
        return "开始日期不能晚于结束日期"

    return None






def get_llm_error_message(error):
    if isinstance(error, APITimeoutError):
        return "大模型请求超时，请稍后重试"

    if isinstance(error, APIConnectionError):
        return "大模型连接失败，请检查网络"

    if isinstance(error, AuthenticationError):
        return "大模型服务认证失败"

    if isinstance(error, RateLimitError):
        return "大模型服务暂时受限，请稍后重试"

    if isinstance(error, json.JSONDecodeError):
        return "大模型返回的数据格式错误"

    if isinstance(error, APIStatusError):
        return "大模型服务暂时不可用"

    return "大模型处理失败，请稍后重试"




if __name__ == "__main__":
    import httpx

    request = httpx.Request(
        "POST", "https://example.com"
    )

    print("超时测试：", get_llm_error_message(
        APITimeoutError(request=request)
    ))

    print("连接测试：", get_llm_error_message(
        APIConnectionError(request=request)
    ))

    print("JSON测试：", get_llm_error_message(
        json.JSONDecodeError("错误数据", "", 0)
    ))

    print("未知异常：", get_llm_error_message(
        Exception("测试异常")
    ))
