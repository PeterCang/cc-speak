#!/usr/bin/env python3
"""
cc-speak: Stop hook — reads aloud the last assistant message via edge-tts.

Stdin: JSON from Claude Code Stop hook
  {"transcript_path": "/path/to/session.jsonl", "session_id": "...", "cwd": "..."}

Always exits 0 — never blocks Claude Code.
TTS is launched in a detached background process (double-fork).
"""

import json
import os
import re
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

CONFIG_PATH = Path.home() / ".config" / "cc-speak" / "config.json"

DEFAULTS = {
    "enabled": True,
    "edge_voice_zh": "zh-CN-XiaoxiaoNeural",
    "edge_voice_en": "en-US-JennyNeural",
    "max_chars": 300,
    "min_chars": 5,
    "log_file": "/tmp/cc-speak.log",
}


def load_config() -> dict:
    cfg = dict(DEFAULTS)
    if CONFIG_PATH.exists():
        try:
            cfg.update(json.loads(CONFIG_PATH.read_text()))
        except Exception:
            pass
    return cfg


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

_log_file: str = ""


def log(msg: str) -> None:
    if not _log_file:
        return
    try:
        with open(_log_file, "a") as f:
            f.write(f"[{datetime.now().strftime('%H:%M:%S')}] cc-speak: {msg}\n")
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Transcript parsing
# ---------------------------------------------------------------------------

def extract_last_assistant_text(transcript_path: str) -> str | None:
    """
    Scan the JSONL transcript in reverse to find the last assistant message
    that contains at least one text block (skips tool-use-only turns).

    JSONL entry format:
      {"type": "assistant", "message": {"content": [{"type": "text", "text": "..."}]},
       "isApiErrorMessage": false, "timestamp": "..."}
    """
    path = Path(transcript_path)
    if not path.exists():
        log(f"transcript not found: {transcript_path}")
        return None

    try:
        with open(path, "rb") as f:
            try:
                f.seek(-65536, 2)
            except OSError:
                f.seek(0)
            tail = f.read().decode("utf-8", errors="replace")
    except Exception as e:
        log(f"failed to read transcript: {e}")
        return None

    for line in reversed(tail.splitlines()):
        line = line.strip()
        if not line or not line.startswith("{"):
            continue
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            continue

        if entry.get("type") != "assistant":
            continue
        if entry.get("isApiErrorMessage"):
            continue

        content = entry.get("message", {}).get("content", [])
        if not isinstance(content, list):
            continue

        text_parts = [
            block["text"]
            for block in content
            if isinstance(block, dict)
            and block.get("type") == "text"
            and isinstance(block.get("text"), str)
            and block["text"].strip()
        ]

        if text_parts:
            return "\n".join(text_parts)

    return None


# ---------------------------------------------------------------------------
# Text preprocessing
# ---------------------------------------------------------------------------

_STRIP_PATTERNS = [
    (re.compile(r"```[\w]*\n.*?```", re.DOTALL), " [代码块] "),
    (re.compile(r"`([^`]+)`"), r"\1"),
    (re.compile(r"^#{1,6}\s+", re.MULTILINE), ""),
    (re.compile(r"\*{1,3}([^*\n]+)\*{1,3}"), r"\1"),
    (re.compile(r"\[([^\]]+)\]\([^)]+\)"), r"\1"),
    (re.compile(r"https?://\S+"), " [链接] "),
    (re.compile(r"^[-*_]{3,}\s*$", re.MULTILINE), ""),
    (re.compile(r"\n{3,}"), "\n\n"),
]


def preprocess_text(text: str, max_chars: int) -> str:
    for pattern, replacement in _STRIP_PATTERNS:
        text = pattern.sub(replacement, text)
    text = re.sub(r"[ \t]+", " ", text).strip()

    if len(text) > max_chars:
        truncated = text[:max_chars]
        last_punct = max(
            truncated.rfind("。"),
            truncated.rfind("！"),
            truncated.rfind("？"),
            truncated.rfind(". "),
            truncated.rfind("! "),
            truncated.rfind("? "),
        )
        if last_punct > max_chars // 2:
            truncated = truncated[: last_punct + 1]
        text = truncated + "…"

    return text


# ---------------------------------------------------------------------------
# Language detection
# ---------------------------------------------------------------------------

def detect_language(text: str) -> str:
    chinese_chars = sum(1 for c in text if "一" <= c <= "鿿")
    return "zh" if chinese_chars / max(len(text), 1) > 0.15 else "en"


# ---------------------------------------------------------------------------
# TTS via edge-tts (cross-platform detached process)
# ---------------------------------------------------------------------------

def speak_edge_tts(text: str, voice: str) -> None:
    """
    Launch edge-tts in a detached background process.
    Uses double-fork on Unix, DETACHED_PROCESS flags on Windows.
    The hook exits immediately; TTS runs independently.
    """
    tmp = tempfile.mktemp(suffix=".mp3", prefix="cc-speak-")

    if sys.platform == "win32":
        # Windows: use CREATE_NO_WINDOW + DETACHED_PROCESS.
        # Use Windows MCI (winmm) via ctypes — supports MP3 natively.
        # Media.SoundPlayer only supports WAV and cannot play edge-tts output.
        script = "\n".join([
            "import subprocess, os, ctypes",
            f"tmp = {repr(tmp)}",
            f"voice = {repr(voice)}",
            f"text = {repr(text)}",
            "ret = subprocess.call(",
            "    ['edge-tts', '--voice', voice, '--text', text, '--write-media', tmp],",
            "    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)",
            "if ret == 0 and os.path.exists(tmp):",
            "    winmm = ctypes.windll.winmm",
            "    winmm.mciSendStringW('open \"' + tmp + '\" type mpegvideo alias cc_speak', None, 0, None)",
            "    winmm.mciSendStringW('play cc_speak wait', None, 0, None)",
            "    winmm.mciSendStringW('close cc_speak', None, 0, None)",
            "    try:",
            "        os.unlink(tmp)",
            "    except OSError:",
            "        pass",
        ])
        subprocess.Popen(
            [sys.executable, "-c", script],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NO_WINDOW,
        )
    else:
        # Unix: double-fork to fully detach from Claude Code's process group
        pid = os.fork()
        if pid == 0:
            os.setsid()
            pid2 = os.fork()
            if pid2 == 0:
                devnull = os.open("/dev/null", os.O_RDWR)
                for fd in (0, 1, 2):
                    os.dup2(devnull, fd)
                os.close(devnull)

                ret = subprocess.call(
                    ["edge-tts", "--voice", voice, "--text", text, "--write-media", tmp],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                if ret == 0 and os.path.exists(tmp):
                    player = "afplay" if sys.platform == "darwin" else "aplay"
                    subprocess.call(
                        [player, tmp],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                    )
                    try:
                        os.unlink(tmp)
                    except OSError:
                        pass
                os._exit(0)
            else:
                os._exit(0)
        else:
            os.waitpid(pid, 0)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    cfg = load_config()

    global _log_file
    _log_file = cfg.get("log_file", "")

    if not cfg.get("enabled", True):
        log("disabled via config")
        sys.exit(0)

    try:
        hook_input = json.loads(sys.stdin.read())
    except Exception as e:
        log(f"failed to parse stdin: {e}")
        sys.exit(0)

    transcript_path = hook_input.get("transcript_path", "")
    if not transcript_path:
        log("no transcript_path in hook input")
        sys.exit(0)

    log(f"transcript: {transcript_path}")

    text = extract_last_assistant_text(transcript_path)
    if not text:
        log("no speakable text found")
        sys.exit(0)

    text = preprocess_text(text, cfg["max_chars"])

    if len(text) < cfg.get("min_chars", 5):
        log(f"text too short ({len(text)} chars), skipping")
        sys.exit(0)

    lang = detect_language(text)
    voice = cfg["edge_voice_zh"] if lang == "zh" else cfg["edge_voice_en"]
    log(f"speaking [{lang}] via {voice}: {text[:80]}…")

    speak_edge_tts(text, voice)
    sys.exit(0)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        try:
            log(f"unhandled exception: {e}")
        except Exception:
            pass
        sys.exit(0)
