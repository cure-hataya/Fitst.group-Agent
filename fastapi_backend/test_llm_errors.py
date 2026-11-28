
import httpx
from unittest.mock import patch
from fastapi.testclient import TestClient
from openai import APIConnectionError
import main

client = TestClient(main.app)

error = APIConnectionError(
    request=httpx.Request("POST", "https://example.com")
)

with patch("main.parse_bill", side_effect=error):
    response = client.post(
        "/llm/recognize",
        json={"text": "昨天吃饭花了25元"}
    )

    print("智能记账异常测试：")
    print(response.status_code)
    print(response.json())

    assert response.status_code == 502
    assert response.json()["success"] is False

with patch("main.llm_parse_query", side_effect=error):
    response = client.post(
        "/llm/query",
        json={"text": "这个月花了多少钱"}
    )

    print("智能查账异常测试：")
    print(response.status_code)
    print(response.json())

    assert response.status_code == 502
    assert response.json()["success"] is False

print("全部异常测试通过！")
