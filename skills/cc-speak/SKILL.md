---
name: install
description: "Install cc-speak: checks for edge-tts, installs it if missing, then sets up the default config. TRIGGERS - /cc-speak:install, install cc-speak, setup cc-speak."
allowed-tools: Bash, Read, Write, Edit
---

# cc-speak Install

Sets up cc-speak so Claude Code reads aloud the last assistant message after
each task completes. The Stop hook is auto-loaded from `hooks/hooks.json` by
the Claude Code plugin system — no `settings.json` registration needed.

## Step 1 — Check Python

```bash
if command -v python3 >/dev/null 2>&1; then
  python3 --version
elif command -v python >/dev/null 2>&1; then
  PY_MAJOR=$(python -c "import sys; print(sys.version_info.major)" 2>/dev/null)
  if [ "$PY_MAJOR" = "3" ]; then
    python --version
  else
    echo "PYTHON_NOT_FOUND"
  fi
else
  echo "PYTHON_NOT_FOUND"
fi
```

If the output is `PYTHON_NOT_FOUND`, tell the user Python 3 is required and stop.

## Step 2 — Check and install edge-tts

```bash
PYTHON=$(command -v python3 2>/dev/null || command -v python 2>/dev/null)
"$PYTHON" -c "import edge_tts; print('edge-tts OK')" 2>/dev/null || echo "EDGE_TTS_MISSING"
```

If the output is `EDGE_TTS_MISSING`, install it now:

```bash
PYTHON=$(command -v python3 2>/dev/null || command -v python 2>/dev/null)
# macOS/Linux may need --break-system-packages; Windows does not
"$PYTHON" -m pip install edge-tts --break-system-packages 2>&1 | grep -v "^note\|^hint\|^warning" || \
"$PYTHON" -m pip install edge-tts 2>&1 | tail -3
"$PYTHON" -c "import edge_tts; print('edge-tts installed OK')" 2>/dev/null || echo "INSTALL_FAILED"
```

If the output is `INSTALL_FAILED`, tell the user to run `python3 -m pip install edge-tts --break-system-packages` manually and stop.

## Step 3 — Verify hook script is executable

```bash
PLUGIN_DIR=$(find "$HOME/.claude/plugins/marketplaces" -maxdepth 1 -name "cc-speak" -type d 2>/dev/null | head -1)
if [ -z "$PLUGIN_DIR" ]; then
  echo "NOT_FOUND"
else
  chmod +x "$PLUGIN_DIR/hooks/stop-speak.py"
  echo "HOOK_READY: $PLUGIN_DIR/hooks/stop-speak.py"
fi
```

If the output is `NOT_FOUND`, tell the user to run `claude plugin marketplace add PeterCang/cc-speak` first and stop.

## Step 4 — Install default config

```bash
CONFIG_DIR="$HOME/.config/cc-speak"
CONFIG_FILE="$CONFIG_DIR/config.json"
PLUGIN_DIR=$(find "$HOME/.claude/plugins/marketplaces" -maxdepth 1 -name "cc-speak" -type d 2>/dev/null | head -1)

if [ ! -f "$CONFIG_FILE" ]; then
  mkdir -p "$CONFIG_DIR"
  cp "$PLUGIN_DIR/config/config.default.json" "$CONFIG_FILE"
  echo "CONFIG_CREATED: $CONFIG_FILE"
else
  echo "CONFIG_EXISTS: $CONFIG_FILE"
fi
```

## Step 5 — Done

Tell the user:

> cc-speak is installed. **Restart Claude Code** for the hook to take effect.
>
> After restarting, Claude will read aloud the last message after each task.
>
> - Config: `~/.config/cc-speak/config.json`
> - Logs: `tail -f /tmp/cc-speak.log`
