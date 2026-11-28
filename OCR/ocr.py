"""OCR 模块（单文件版）：图片 / 语音 → 结构化账目。
用法：
    from ocr import recognize, transcribe

    result = recognize(image_bytes)
    if result["ok"]:
        print(result["amount"], result["category"])

返回不抛异常：
    {"ok": True,  "source": "image", "amount": 38.5, ...}
    {"ok": False, "source": "image", "error": {"code": "NO_AMOUNT", "message": "..."}}
"""
from __future__ import annotations

import base64
import io
import json
import os
import re
from pathlib import Path
from typing import Any

# 配置
try:
    from dotenv import load_dotenv

    def _load_env() -> None:

        here = Path(__file__).resolve().parent
        for base in [here, *here.parents][:5]:
            candidate = base / ".env"
            if candidate.exists():
                load_dotenv(candidate)
                return

    _load_env()
except Exception:
    pass

#直接粘 Key
# 优先级：LOCAL_API_KEY > 环境变量 > .env
API_KEY = (LOCAL_API_KEY or os.getenv("DASHSCOPE_API_KEY", "")).strip()
BASE_URL = os.getenv("DASHSCOPE_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")
VISION_MODEL = os.getenv("VISION_MODEL", "qwen3-vl-plus")
ASR_MODEL = os.getenv("ASR_MODEL", "qwen3-asr-flash")
TEXT_MODEL = os.getenv("TEXT_MODEL", "qwen-plus")

CATEGORIES = ["餐饮", "交通", "购物", "居住", "娱乐", "医疗", "教育", "人情", "其他"]

MAX_EDGE = 2000
MAX_IMAGE_BYTES = 8 * 1024 * 1024
MAX_AUDIO_BYTES = 20 * 1024 * 1024
IMAGE_MIME = {"image/jpeg", "image/png", "image/webp"}
AUDIO_MIME = {
    "audio/wav", "audio/x-wav", "audio/wave", "audio/mpeg", "audio/mp3",
    "audio/mp4", "audio/x-m4a", "audio/m4a", "audio/webm", "audio/ogg",
}

# 提示词
OCR_PROMPT = """你是小票识别模块。读出这张小票/支付截图里的信息，只输出 JSON：

{"amount": 数字或 null,
 "merchant": "商户名或 null",
 "date": "YYYY-MM-DD 或 null",
 "category": "餐饮/交通/购物/居住/娱乐/医疗/教育/人情/其他",
 "items": ["商品1", "商品2"],
 "confidence": 0~1}

注意：
- amount 只取最终实付金额，优先「实付/合计/总计」，不要取商品单价、找零、优惠前金额。
- 看不清就填 null，不要猜。
- 只输出 JSON，不要解释。"""

TEXT_PROMPT = """把这句话转成记账 JSON，只输出 JSON：

{"amount": 数字或 null, "category": "餐饮/交通/购物/居住/娱乐/医疗/教育/人情/其他",
 "date_text": "原样抄写时间词，如「昨天」「11月1号」，没说就填「今天」",
 "note": "原句"}

不要自己换算日期。"""


# 工具
def available() -> bool:
    """有 Key 且看起来像真的（防止把占位文字当 Key）。"""
    return API_KEY.startswith("sk-") and len(API_KEY) > 12


def _client():
    if not API_KEY:
        raise RuntimeError("没有配置 DASHSCOPE_API_KEY")
    from openai import OpenAI

    return OpenAI(api_key=API_KEY, base_url=BASE_URL, timeout=60)


def _strip_fence(text: str) -> str:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```[a-zA-Z]*\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)
    return cleaned.strip()


def _parse_json(text: str) -> dict[str, Any]:
    return json.loads(_strip_fence(text))


def prepare_image(data: bytes) -> bytes:
    """EXIF 转正 + 长边压到 2000px + 转 JPEG。"""
    from PIL import Image, ImageOps

    if len(data) > MAX_IMAGE_BYTES:
        raise ValueError("图片超过 8MB")
    image = ImageOps.exif_transpose(Image.open(io.BytesIO(data))).convert("RGB")
    if max(image.size) > MAX_EDGE:
        image.thumbnail((MAX_EDGE, MAX_EDGE))
    buffer = io.BytesIO()
    image.save(buffer, format="JPEG", quality=88)
    return buffer.getvalue()


def _recognize_image(data: bytes) -> dict[str, Any]:
    jpeg = prepare_image(data)
    b64 = base64.b64encode(jpeg).decode("ascii")
    resp = _client().chat.completions.create(
        model=VISION_MODEL,
        messages=[{
            "role": "user",
            "content": [
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}},
                {"type": "text", "text": OCR_PROMPT},
            ],
        }],
        temperature=0.1,
    )
    raw = resp.choices[0].message.content
    result = _parse_json(raw)
    result["raw"] = raw
    result.setdefault("amount", None)
    result.setdefault("confidence", 0.6)
    if result.get("category") not in CATEGORIES:
        result["category"] = "其他"
    return result


def _speech_to_text(data: bytes, mime: str) -> str:
    resp = _client().chat.completions.create(
        model=ASR_MODEL,
        messages=[{
            "role": "user",
            "content": [{
                "type": "input_audio",
                "input_audio": {"data": f"data:{mime};base64,{base64.b64encode(data).decode('ascii')}"},
            }],
        }],
        stream=False,
        extra_body={"asr_options": {"language": "zh", "enable_itn": True}},
    )
    content = resp.choices[0].message.content
    if isinstance(content, list):
        content = "".join(i.get("text", "") if isinstance(i, dict) else str(i) for i in content)
    return str(content).strip()


def _text_to_record(text: str) -> dict[str, Any]:
    resp = _client().chat.completions.create(
        model=TEXT_MODEL,
        messages=[{"role": "user", "content": f"{TEXT_PROMPT}\n\n输入：{text}"}],
        temperature=0.1,
        response_format={"type": "json_object"},
    )
    record = _parse_json(resp.choices[0].message.content)
    if record.get("category") not in CATEGORIES:
        record["category"] = "其他"
    return record


# 对外接口
def _ok(source: str, **fields: Any) -> dict[str, Any]:
    base = {
        "ok": True, "source": source, "amount": None, "occurred_on": None,
        "category": "其他", "subcategory": None, "merchant": None,
        "note": None, "confidence": 0.0, "raw": None, "error": None,
    }
    base.update(fields)
    return base


def _err(source: str, code: str, message: str) -> dict[str, Any]:
    return {"ok": False, "source": source, "error": {"code": code, "message": message}}


def recognize(image: bytes, *, mime: str = "image/jpeg") -> dict[str, Any]:
    """图片 → 待确认的账目"""
    try:
        if not available():
            return _err("image", "NO_KEY", "服务端未配置有效的 DASHSCOPE_API_KEY")
        if not image:
            return _err("image", "EMPTY", "图片是空的")
        if mime not in IMAGE_MIME:
            return _err("image", "UNSUPPORTED_TYPE", f"不支持的图片格式：{mime}")
        if len(image) > MAX_IMAGE_BYTES:
            return _err("image", "TOO_LARGE", "图片超过 8MB，请先压缩")

        result = _recognize_image(image)
        amount = result.get("amount")
        if amount in (None, 0, "0", ""):
            return _err("image", "NO_AMOUNT", "没能从小票上读出金额，请手工填写")

        return _ok(
            "image",
            amount=round(float(amount), 2),
            occurred_on=result.get("date") or None,
            category=result.get("category") or "其他",
            merchant=result.get("merchant") or None,
            note="、".join(result.get("items") or []) or result.get("merchant"),
            confidence=float(result.get("confidence") or 0.6),
            raw=result.get("raw"),
        )
    except Exception as exc:
        return _err("image", "MODEL_ERROR", f"{type(exc).__name__}: {exc}"[:200])


def transcribe(audio: bytes, *, mime: str = "audio/wav") -> dict[str, Any]:
    """语音 → 待确认的账目。"""
    try:
        if not available():
            return _err("audio", "NO_KEY", "服务端未配置有效的 DASHSCOPE_API_KEY")
        if not audio:
            return _err("audio", "EMPTY", "音频是空的")
        if mime not in AUDIO_MIME:
            return _err("audio", "UNSUPPORTED_TYPE", f"不支持的音频格式：{mime}")
        if len(audio) > MAX_AUDIO_BYTES:
            return _err("audio", "TOO_LARGE", "音频超过 20MB")

        text = _speech_to_text(audio, mime)
        record = _text_to_record(text) if text else {}
        return _ok("audio", amount=record.get("amount"), category=record.get("category") or "其他",
                   note=record.get("note") or text, confidence=0.7, raw=text)
    except Exception as exc:
        return _err("audio", "MODEL_ERROR", f"{type(exc).__name__}: {exc}"[:200])


__all__ = ["recognize", "transcribe", "available", "CATEGORIES"]
