import logging
import os
from typing import List, Tuple


def split_sse_chunks(line: str) -> Tuple[List[str], str]:
    """Split a line that may contain multiple JSON objects into individual chunks.
    Returns (list of complete JSON strings, remainder for next read)."""
    out = []
    rest = line.strip()
    if rest.startswith("data:"):
        rest = rest[5:].strip()
    while rest and rest != "[DONE]":
        rest = rest.lstrip()
        if not rest:
            break
        if rest == "[DONE]":
            return (out, "")
        depth = 0
        in_str = False
        escape = False
        end = -1
        for i, c in enumerate(rest):
            if escape:
                escape = False
                continue
            if c == "\\" and in_str:
                escape = True
                continue
            if in_str:
                if c == '"':
                    in_str = False
                continue
            if c == '"':
                in_str = True
                continue
            if c == "{":
                depth += 1
            elif c == "}":
                depth -= 1
                if depth == 0:
                    end = i + 1
                    break
        if end > 0:
            out.append(rest[:end])
            rest = rest[end:].lstrip()
        else:
            return (out, rest)
    return (out, rest)


def str2bool(val):
    return str(val).lower() in ("1", "true", "yes", "on")


app_logger = logging.getLogger(__name__)
app_logger.setLevel(logging.getLevelName(os.getenv("LOG_LEVEL", "INFO")))
app_handler = logging.StreamHandler()
app_formatter = logging.Formatter("%(name)s %(asctime)s %(levelname)s %(message)s")
app_handler.setFormatter(app_formatter)
app_logger.addHandler(app_handler)