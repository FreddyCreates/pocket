"""Polish agent replies so POCKET chat looks human, not like a raw CLI dump."""

from __future__ import annotations

import re
from typing import Optional

# Common mojibake / bad UTF-8 sequences from Windows consoles and JSON round-trips
_MOJIBAKE = (
    ("\u2018", "'"),
    ("\u2019", "'"),
    ("\u201c", '"'),
    ("\u201d", '"'),
    ("\u2013", "-"),
    ("\u2014", "—"),
    ("\u2026", "..."),
    ("\u00a0", " "),
    ("â€™", "'"),
    ("â€˜", "'"),
    ("â€œ", '"'),
    ("â€\x9d", '"'),
    ("â€œ", '"'),
    ("â€\x9c", '"'),
    ("â€”", "—"),
    ("â€“", "-"),
    ("â€¦", "..."),
    ("Ã—", "x"),
    ("Â·", "·"),
    ("Â ", " "),
    ("â†'", "→"),
    ("â†’", "→"),
    ("�?`", "—"),
    ("�?", "'"),
    ("�?o", '"'),
    ("�??", '"'),
    ("�?T", "'"),
    ("�?`", "'"),
)

# Codex / Grok CLI chrome (drop from chat body; keep substance)
_BANNER_LINE = re.compile(
    r"^(?:"
    r"Reading additional input from stdin\.{0,3}"
    r"|OpenAI Codex v[\d.]+"
    r"|-{3,}"
    r"|workdir:\s*.+"
    r"|model:\s*.+"
    r"|provider:\s*.+"
    r"|approval:\s*.+"
    r"|sandbox:\s*.+"
    r"|reasoning (?:effort|summaries):\s*.+"
    r"|session id:\s*.+"
    r"|tokens used"
    r"|\d{1,3}(?:,\d{3})*\s*$"  # lone token counts
    r"|user\s*$"
    r"|codex\s*$"
    r"|\[stream_tokens[^\]]*\]"
    r"|\[llm_tokens[^\]]*\]"
    r"|\[pocket_session[^\]]*\]"
    r"|\[engine=[^\]]+\]"
    r"|\[cli=[^\]]+\]"
    r"|\[research_package=[^\]]+\]"
    r")\s*$",
    re.I,
)

_ENGINE_META = re.compile(
    r"^\[(?:engine|cli|research_package|pocket_session|stream_tokens|llm_tokens)[^\]]*\]\s*$",
    re.I | re.M,
)

# Progress blobs stuck together: "you.Treating this" / "next.Shipping the"
_RUNON = re.compile(r"([.!?])([A-Z][a-z])")

# Tool chatter noise lines (keep short tool summaries if mixed with prose)
_NOISE_PREFIX = re.compile(
    r"^(?:exec|bash|shell_command|apply_patch|Succeeded in|Exit code:|Wall time:)\b",
    re.I,
)


def fix_encoding(text: str) -> str:
    s = text or ""
    for bad, good in _MOJIBAKE:
        if bad in s:
            s = s.replace(bad, good)
    # Drop lone replacement chars that are pure noise
    s = s.replace("\ufffd", "")
    return s


def _is_banner_line(line: str) -> bool:
    t = line.strip()
    if not t:
        return False
    if _BANNER_LINE.match(t):
        return True
    if t.startswith("--------"):
        return True
    return False


def strip_cli_chrome(text: str) -> str:
    """Remove Codex/Grok CLI banners and POCKET meta headers from chat body."""
    if not text:
        return ""
    lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    kept: list[str] = []
    skip_user_block = False
    for line in lines:
        stripped = line.strip()
        if stripped.lower() == "user":
            # Drop the echoed "user" + next client-device blob block when it's pure echo
            skip_user_block = True
            continue
        if skip_user_block:
            if stripped.lower() in ("codex", "assistant", "thinking") or stripped.startswith("["):
                skip_user_block = False
                if stripped.lower() in ("codex",):
                    continue
            elif stripped.startswith("[Client device:"):
                continue
            elif not stripped:
                skip_user_block = False
                continue
            else:
                # Real content after user label — keep
                skip_user_block = False
        if _is_banner_line(line):
            continue
        if _ENGINE_META.match(stripped):
            continue
        kept.append(line)

    # Collapse huge runs of blank lines
    out: list[str] = []
    blank = 0
    for line in kept:
        if not line.strip():
            blank += 1
            if blank <= 2:
                out.append("")
            continue
        blank = 0
        out.append(line)
    body = "\n".join(out).strip()
    # Drop a leading one-line user-echo fragment when a real answer follows
    blines = body.split("\n")
    if len(blines) >= 3 and len(blines[0].strip()) < 120 and not blines[0].strip().startswith(("#", "-", "*", "•")):
        rest = "\n".join(blines[1:]).strip()
        if len(rest) > len(blines[0]) * 2 and (
            rest.startswith("#")
            or rest.startswith("-")
            or rest.startswith("**")
            or "\n- " in rest
            or "tests pass" in rest.lower()
            or "fixed" in rest.lower()
            or "changed" in rest.lower()
        ):
            body = rest
    return body


def break_runons(text: str) -> str:
    """Insert paragraph breaks when streams glue sentences without newlines."""
    if not text:
        return ""
    # Only apply when there are very few newlines (streaming dump)
    if text.count("\n") >= max(4, len(text) // 400):
        return text
    return _RUNON.sub(r"\1\n\n\2", text)


def extract_substance(text: str) -> str:
    """
    Prefer the final human summary after tool noise when present.
    Keeps full text when it's already clean prose.
    """
    if not text or len(text) < 80:
        return text
    # After last "tokens used" block, Codex often prints the real summary
    parts = re.split(r"(?i)\ntokens used\n[\d,]+\s*\n", text)
    if len(parts) >= 2 and len(parts[-1].strip()) > 40:
        return parts[-1].strip()
    return text


def polish_agent_output(text: str, *, engine: str = "", max_chars: int = 60000) -> str:
    """
    Chat-ready agent reply:
    - fix encoding
    - strip CLI chrome / meta headers
    - unstick run-on stream lines
    - keep a compact POCKET footer note if present
    """
    raw = fix_encoding(text or "")
    if not raw.strip():
        return ""

    # Preserve POCKET footer notes
    foot = ""
    m = re.search(r"(\n\n\[POCKET\][^\n]*(?:\n(?!\[)[^\n]*)*)\s*$", raw)
    if m:
        foot = m.group(1).strip()
        raw = raw[: m.start()].rstrip()

    body = strip_cli_chrome(raw)
    body = extract_substance(body)
    body = break_runons(body)
    body = re.sub(r"\n{3,}", "\n\n", body).strip()

    # Soft trim tool-log walls: if >80% lines look like tool noise, keep last 40%
    lines = body.split("\n")
    if len(lines) > 40:
        noise = sum(1 for ln in lines if _NOISE_PREFIX.match(ln.strip()) or ln.strip().startswith("+"))
        if noise / len(lines) > 0.55:
            body = "\n".join(lines[int(len(lines) * 0.55) :]).strip()

    if foot:
        body = (body + "\n\n" + foot).strip() if body else foot

    if len(body) > max_chars:
        body = body[: max_chars - 20].rstrip() + "\n\n…(truncated)"
    return body or (text or "")[-4000:]


def meta_header(engine: str = "", cwd: str = "", extra: Optional[str] = None) -> str:
    """Optional one-line meta for details UI — not dumped as main prose."""
    bits = []
    if engine:
        bits.append(engine)
    if cwd:
        bits.append(cwd)
    if extra:
        bits.append(extra)
    return " · ".join(bits)
