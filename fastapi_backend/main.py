
from fastapi.exceptions import RequestValidationError
from fastapi.encoders import jsonable_encoder

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


from response_service import success_response, error_response


from duplicate_service import find_duplicate


from validation_service import validate_expense, validate_expense_date



from category_service import normalize_category, STANDARD_CATEGORIES



from llm_service import parse_bill, validate_query, get_llm_error_message

from llm_service import parse_query as llm_parse_query




import re
from datetime import date,timedelta
from fastapi import FastAPI
app=FastAPI()

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc):
    detail = exc.detail

    if isinstance(detail, dict):
        message = detail.get("message", "操作失败")
        data = detail
    else:
        message = str(detail)
        data = None

    response = error_response(message, data)
    response["detail"] = detail

    return JSONResponse(
        status_code=exc.status_code,
        content=response,
        headers=exc.headers
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc):
    errors = jsonable_encoder(exc.errors())

    response = error_response(
        "请求参数校验失败",
        errors
    )

    response["detail"] = errors

    return JSONResponse(
        status_code=422,
        content=response
    )



@app.get("/")
def home():
    return{"message":"AI智能记账助手后端启动成功！"}
from pydantic import BaseModel


def classify_expense(item: str) -> str:
    """根据消费项目自动判断类别"""
    item = item.lower()

    if any(word in item for word in ["饭", "餐", "奶茶", "咖啡", "外卖"]):
        return "餐饮"

    elif any(word in item for word in ["打车", "地铁", "公交", "出租车", "高铁"]):
        return "交通"

    elif any(word in item for word in ["教材", "课本", "学费", "课程", "文具"]):
        return "学习"

    elif any(word in item for word in ["买药", "医院", "挂号", "体检", "诊所"]):
        return "医疗"

    elif any(word in item for word in ["房租", "水费", "电费", "话费", "纸巾", "洗衣液"]):
        return "生活"

    elif any(word in item for word in ["衣服", "鞋", "购物", "超市"]):
        return "购物"

    elif any(word in item for word in ["电影", "游戏", "唱歌"]):
        return "娱乐"

    else:
        return "其他"


class Record(BaseModel):
    item: str
    money: float

@app.post("/add")
def add_record(record: Record, force: bool = False):
        error = validate_expense(record.item, record.money)

        if error is not None:
            raise HTTPException(
                status_code=400,
                detail=error
            )

        today = date.today().isoformat()

        duplicate = find_duplicate(
            records,
            record.item,
            record.money,
            today
        )

        if duplicate is not None and not force:
            raise HTTPException(
                status_code=409,
                detail={
                    "message": "发现疑似重复账单，请确认是否继续保存",
                    "duplicate": duplicate
                }
            )

        category = classify_expense(record.item)

        new_record = {
            "id": max((r["id"] for r in records), default=0) + 1,
            "item": record.item.strip(),
            "money": record.money,
            "category": category,
            "date": today
        }

        records.append(new_record)

        response = success_response("添加成功", new_record)
        response["record"] = new_record

        return response


# 临时保存账单数据
records = []

@app.get("/records")
def get_records():
    return {
        "message": "查询成功",
        "records": records
    }

from fastapi import HTTPException

@app.delete("/records/{record_id}")
def delete_record(record_id: int):
    for record in records:
        if record["id"] == record_id:
            records.remove(record)

            response = success_response(
                "删除成功",
                {"deleted_id": record_id}
            )
            response["deleted_id"] = record_id

            return response


    raise HTTPException(
        status_code=404,
        detail="没有找到这笔账单"
    )

@app.put("/records/{record_id}")

def update_record(record_id: int, updated: Record):
    error = validate_expense(updated.item, updated.money)

    if error is not None:
        raise HTTPException(
            status_code=400,
            detail=error
        )

    for record in records:

        if record["id"] == record_id:
            record["item"] = updated.item
            record["money"] = updated.money
            record["category"] = classify_expense(updated.item)

            response = success_response("修改成功", record)
            response["record"] = record

            return response

    raise HTTPException(
        status_code=404,
        detail="没有找到这笔账单"
    )

@app.get("/statistics")
def get_statistics():
    total = sum(record["money"] for record in records)

    return {
        "total_money": round(total, 2),
        "record_count": len(records)
    }

@app.get("/statistics/category")
def category_statistics():
    result = {}

    for record in records:
        category = record.get("category", "其他")
        money = record["money"]

        result[category] = result.get(category, 0) + money

    return {
        category: round(money, 2)
        for category, money in result.items()
    }

@app.get("/statistics/time")
def time_statistics():
    today = date.today()
    week_start = today - timedelta(days=today.weekday())
    month_start = today.replace(day=1)

    today_total = 0
    week_total = 0
    month_total = 0

    for record in records:
        if "date" not in record:
            continue

        record_date = date.fromisoformat(record["date"])
        money = record["money"]

        if record_date == today:
            today_total += money

        if week_start <= record_date <= today:
            week_total += money

        if month_start <= record_date <= today:
            month_total += money

    return {
        "today": round(today_total, 2),
        "week": round(week_total, 2),
        "month": round(month_total, 2)
    }
class TextRecord(BaseModel):
    text: str


def parse_expense(text: str):
    match = re.search(r"(\d+(?:\.\d+)?)\s*(?:块钱|块|元)", text)

    if not match:
        raise HTTPException(
            status_code=400,
            detail="未识别到消费金额"
        )

    money = float(match.group(1))

    item = text[:match.start()]
    item = re.sub(r"今天|昨天|前天|花了|花费|花|消费了", "", item)
    item = item.strip()

    category = classify_expense(item)

    return {
        "item": item,
        "money": money,
        "category": category
    }



@app.post("/add/text")
def add_text_record(request: TextRecord):
    data = parse_expense(request.text)

    record = Record(
        item=data["item"],
        money=data["money"]
    )

    result = add_record(record)
    result["record"]["date"] = parse_date(request.text)

    return result



def parse_query(text: str):
    period = "all"
    category = None

    if "今天" in text or "今日" in text:
        period = "today"
    elif "昨天" in text or "昨日" in text:
        period = "yesterday"
    elif "前天" in text:
        period = "day_before_yesterday"
    elif "本周" in text or "这周" in text:
        period = "week"
    elif "本月" in text or "这个月" in text:
        period = "month"

    for name in ["餐饮", "交通", "购物", "娱乐", "其他"]:
        if name in text:
            category = name
            break

    return {
        "period": period,
        "category": category
    }


@app.post("/query")
def query_records(request: TextRecord):
    conditions = parse_query(request.text)

    period = conditions["period"]
    category = conditions["category"]

    today = date.today()
    week_start = today - timedelta(days=today.weekday())
    month_start = today.replace(day=1)

    filtered_records = []

    for record in records:
        if category and record.get("category") != category:
            continue

        if period != "all":
            if "date" not in record:
                continue

            record_date = date.fromisoformat(record["date"])

            if period == "today" and record_date != today:
                continue

            if period == "yesterday" and record_date != today - timedelta(days=1):
                continue

            if period == "day_before_yesterday" and record_date != today - timedelta(days=2):
                continue


            if period == "week" and not (
                week_start <= record_date <= today
            ):
                continue

            if period == "month" and not (
                month_start <= record_date <= today
            ):
                continue

        filtered_records.append(record)

    total = sum(r["money"] for r in filtered_records)

    return {
        "question": request.text,
        "period": period,
        "category": category,
        "total_money": round(total, 2),
        "record_count": len(filtered_records),
        "records": filtered_records
    }

def parse_date(text: str):
    today = date.today()

    if "前天" in text:
        return (today - timedelta(days=2)).isoformat()

    elif "昨天" in text:
        return (today - timedelta(days=1)).isoformat()

    else:
        return today.isoformat()

class OCRConfirmRecord(BaseModel):
    item: str
    money: float
    category: str
    date: date

@app.post("/ocr/confirm")

def confirm_ocr_bill(record: OCRConfirmRecord, force: bool = False):


    error = validate_expense(record.item, record.money)

    if error is not None:
        raise HTTPException(
            status_code=400,
            detail=error
        )


    date_error = validate_expense_date(record.date)

    if date_error is not None:
        raise HTTPException(
            status_code=400,
            detail=date_error
        )


    duplicate = find_duplicate(
        records,
        record.item,
        record.money,
        record.date.isoformat()
    )

    if duplicate is not None and not force:
        raise HTTPException(
            status_code=409,
            detail={
                "message": "发现疑似重复账单，请确认是否继续保存",
                "duplicate": duplicate
            }
        )


    new_record = {
        "id": max((r["id"] for r in records), default=0) + 1,
        "item": record.item.strip(),
        "money": record.money,

        "category": normalize_category(record.category),

        "date": record.date.isoformat()
    }

    records.append(new_record)


    response = success_response(
        "OCR账单确认成功",
        new_record
    )

    response["record"] = new_record

    return response




@app.post("/llm/recognize")
def recognize_llm(record: TextRecord):
    if not record.text.strip():
        raise HTTPException(
            status_code=400,
            detail="消费描述不能为空"
        )

    try:
        result = parse_bill(record.text)

    except Exception as e:
        raise HTTPException(
            status_code=502,
            detail=get_llm_error_message(e)
        )

    if result["success"]:
        response = success_response(
            result["message"],
            result["bill"]
        )
    else:
        response = error_response(
            result["message"],
            result.get("bill")
        )

    response["bill"] = result.get("bill")

    return response




def filter_query_records(query):
    result = []

    start = query.get("start_date")
    end = query.get("end_date")
    category = query.get("category")

    for record in records:
        record_date = record.get("date")

        if start is not None:
            if not record_date:
                continue

            if not start <= str(record_date) <= end:
                continue

        if category is not None:
            if record.get("category") != category:
                continue

        result.append(record)

    return result


def calculate_query_result(filtered_records, metric):
    total = sum(r["money"] for r in filtered_records)
    count = len(filtered_records)

    if metric == "total":
        return round(total, 2)

    if metric == "count":
        return count

    if metric == "average":
        return round(total / count, 2) if count else 0

    if metric == "top_category":
        category_totals = {}

        for record in filtered_records:
            category = record["category"]
            category_totals[category] = (
                category_totals.get(category, 0)
                + record["money"]
            )

        if not category_totals:
            return None

        top = max(category_totals, key=category_totals.get)

        return {
            "category": top,
            "money": round(category_totals[top], 2)
        }

    return None

@app.post("/llm/query")
def query_llm(record: TextRecord):
    if not record.text.strip():
        raise HTTPException(
            status_code=400,
            detail="查询内容不能为空"
        )

    try:

        query = llm_parse_query(record.text)



    except Exception as e:

        raise HTTPException(

            status_code=502,

            detail=get_llm_error_message(e)

        )

    error = validate_query(query)

    if error is not None:
        return {
            "success": False,
            "message": error
        }


    category = query.get("category")

    if category is not None:
        normalized = normalize_category(category)

        if normalized == "其他" and category.strip() != "其他":
            return {
                "success": False,
                "message": "无法识别查询的消费类别"
            }

        query["category"] = normalized

    filtered_records = filter_query_records(query)


    result = calculate_query_result(
        filtered_records,
        query["metric"]
    )


    answer = generate_query_answer(
        query,
        result,
        len(filtered_records)
    )


    data = {
        "query": query,
        "count": len(filtered_records),
        "result": result,
        "answer": answer
    }

    response = success_response("查询成功", data)

    response.update(data)

    return response


def generate_query_answer(query, result, count):
    metric = query["metric"]
    category = query.get("category") or "全部"

    start = query.get("start_date")
    end = query.get("end_date")

    if start and end:
        period = f"{start}至{end}"
    else:
        period = "全部历史期间"

    if count == 0:
        return f"您在{period}没有符合条件的消费记录。"

    if metric == "total":
        return (
            f"您在{period}共有{count}笔"
            f"{category}消费，累计支出{result:.2f}元。"
        )

    if metric == "count":
        return f"您在{period}共有{count}笔{category}消费。"

    if metric == "average":
        return (
            f"您在{period}的{category}消费"
            f"平均每笔为{result:.2f}元。"
        )

    if metric == "top_category":
        return (
            f"您在{period}消费最多的类别是"
            f"{result['category']}，"
            f"累计支出{result['money']:.2f}元。"
        )

    return "暂时无法生成查询回答。"
