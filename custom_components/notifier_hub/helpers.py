from __future__ import annotations

import re
from typing import Any

TRUE_VALUES = {"true", "on", "yes", "1"}
FALSE_VALUES = {"false", "off", "no", "0"}


def check_bool(value: Any) -> bool:
    return str(value).lower() in TRUE_VALUES


def check_notify(value: Any) -> bool:
    return not (str(value).lower() in FALSE_VALUES or value == 0)


def return_list(value: Any) -> list[str]:
    if value is None or value == "":
        return []
    if isinstance(value, list):
        return [str(v).strip() for v in value if str(v).strip()]
    if isinstance(value, (tuple, set)):
        return [str(v).strip() for v in value if str(v).strip()]
    return [v.strip() for v in str(value).split(",") if v.strip()]


def replace_regular(text: Any, substitutions: list[tuple[str, str]]) -> str:
    result = str(text or "").strip()
    for old, new in substitutions:
        result = re.sub(re.compile(old), new, result)
    return result


def remove_tags(text: Any) -> str:
    return re.sub(re.compile(r"<.*?>"), "", str(text or "").strip())


def has_numbers(text: Any) -> bool:
    return re.search(r"\d{2}:\d{2}|\d{4,}|\d{3,}\.\d", str(text or "")) is not None


def service_name(notify_name: str) -> str:
    item = notify_name.strip().lower()
    if item.startswith("notify."):
        item = item.replace("notify.", "", 1)
    item = re.sub(r"\s+", "_", item)
    item = item.replace(".", "_").replace("/", "_")
    return item


def normalize_notify_list(value: Any, defaults: list[str]) -> list[str]:
    if value is True or str(value).lower() in TRUE_VALUES or value == "":
        return defaults
    if not check_notify(value):
        return []
    return return_list(value)


def estimate_speech_duration(text: str, wait_time: float) -> float:
    clean = remove_tags(text)
    words = len(clean.split()) or 1
    chars = len(clean)
    duration = (words * 0.007) * 60
    if has_numbers(clean):
        duration += 4
    if (chars / words) > 7 and chars > 90:
        duration += 7
    return max(1.0, duration + wait_time)
