from __future__ import annotations
import re
from dataclasses import dataclass
from typing import Optional

@dataclass
class Segment:
    kind: str
    text: str
    prefix: str = ""
    suffix: str = ""
    inner_kind: Optional[str] = None

_MD_FENCE = re.compile(r"```(?P<lang>[a-zA-Z0-9_+-]+)?\n(?P<body>.*?)\n```\s*\Z", re.DOTALL)
_PY_HEREDOC = re.compile(
    r"(?P<prefix>.*?python\s+-\s+<<['\"]?PY['\"]?\n)"
    r"(?P<body>.*?)"
    r"(?P<suffix>\nPY\s*)\Z",
    re.DOTALL | re.IGNORECASE,
)

def regex_segment(text: str) -> list[Segment]:
    m = _PY_HEREDOC.match(text)
    if m:
        return [Segment(kind="bash_python_heredoc", text=m.group("body"), prefix=m.group("prefix"), suffix=m.group("suffix"), inner_kind="python")]

    m2 = _MD_FENCE.match(text.strip())
    if m2:
        lang = (m2.group("lang") or "").lower()
        inner = lang if lang else None
        return [Segment(kind="markdown_fence", text=m2.group("body"), prefix=f"```{m2.group('lang') or ''}\n", suffix="\n```", inner_kind=inner)]

    return [Segment(kind="raw", text=text)]
