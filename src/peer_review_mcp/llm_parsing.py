import json
import re
from typing import Any


def strip_code_fences(text: str) -> str:
    cleaned = text.strip()
    if cleaned.startswith("```json"):
        cleaned = cleaned[7:]
    elif cleaned.startswith("```"):
        cleaned = cleaned[3:]
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]
    return cleaned.strip()


def _extract_fenced_block(text: str) -> str | None:
    if "```json" in text:
        start = text.find("```json") + 7
        end = text.find("```", start)
        if end != -1:
            return text[start:end].strip()
    if "```" in text:
        start = text.find("```") + 3
        end = text.find("```", start)
        if end != -1:
            return text[start:end].strip()
    return None


def _extract_braced_block(text: str) -> str | None:
    obj_start = text.find("{")
    obj_end = text.rfind("}")
    if obj_start != -1 and obj_end != -1 and obj_end > obj_start:
        return text[obj_start : obj_end + 1]
    arr_start = text.find("[")
    arr_end = text.rfind("]")
    if arr_start != -1 and arr_end != -1 and arr_end > arr_start:
        return text[arr_start : arr_end + 1]
    return None


def try_parse_json(text: str) -> Any | None:
    try:
        return json.loads(strip_code_fences(text))
    except Exception:
        pass

    fenced = _extract_fenced_block(text)
    if fenced:
        try:
            return json.loads(fenced)
        except Exception:
            pass

    braced = _extract_braced_block(text)
    if braced:
        try:
            return json.loads(braced)
        except Exception:
            pass

    return None


def strip_markdown(text: str) -> str:
    lines = text.splitlines()
    cleaned_lines: list[str] = []
    in_code_block = False

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("```"):
            in_code_block = not in_code_block
            continue
        if in_code_block:
            continue

        line = re.sub(r"^\s{0,3}#{1,6}\s+", "", line)
        line = re.sub(r"^\s*[-*+•]\s+", "", line)
        line = re.sub(r"^\s*\d+[.)]\s+", "", line)
        cleaned_lines.append(line.strip())

    cleaned = " ".join(part for part in cleaned_lines if part)
    cleaned = cleaned.replace("`", "")
    cleaned = cleaned.replace("**", "").replace("*", "").replace("_", "")
    cleaned = re.sub(r"\s{2,}", " ", cleaned).strip()
    return cleaned
