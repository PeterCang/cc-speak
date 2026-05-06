---
name: install
description: "Install cc-speak: checks for edge-tts, installs it if missing, then registers the Stop hook. TRIGGERS - /cc-speak:install, install cc-speak, setup cc-speak."
allowed-tools: Bash, Read, Write, Edit
---

# cc-speak Install

Sets up the cc-speak Stop hook so Claude Code reads aloud the last assistant
message after each task completes.

## Step 1 — Check Python

```bash
python3 --version 2>/dev/null || echo "PYTHON_NOT_FOUND"
```

If the output is `PYTHON_NOT_FOUND`, tell the user Python 3 is required and stop.

## Step 2 — Check and install edge-tts

```bash
python3 -c "import edge_tts; print('edge-tts OK')" 2>/dev/null || echo "EDGE_TTS_MISSING"
```

If the output is `EDGE_TTS_MISSING`, install it now:

```bash
pip install edge-tts 2>&1 | tail -3
python3 -c "import edge_tts; print('edge-tts installed OK')" 2>/dev/null || echo "INSTALL_FAILED"
```

If the output is `INSTALL_FAILED`, tell the user to run `pip install edge-tts` manually and stop.

## Step 3 — Locate plugin directory

```bash
PLUGIN_DIR=$(find "$HOME/.claude/plugins/marketplaces" -maxdepth 1 -name "cc-speak" -type d 2>/dev/null | head -1)
if [ -z "$PLUGIN_DIR" ]; then
  PLUGIN_DIR=$(find "$HOME/.claude/plugins/cache" -path "*/cc-speak/cc-speak/*/hooks/stop-speak.py" 2>/dev/null | head -1 | xargs -I{} dirname {} 2>/dev/null | xargs -I{} dirname {} 2>/dev/null)
fi
echo "${PLUGIN_DIR:-NOT_FOUND}"
```

Use the path printed above as `PLUGIN_DIR` in the next step.
If `NOT_FOUND`, tell the user to run `claude plugin marketplace add PeterCang/cc-speak` first and stop.

## Step 4 — Register Stop hook in settings.json

Run this Python script, replacing `PLUGIN_DIR_PLACEHOLDER` with the actual path from Step 3:

```bash
PLUGIN_DIR=$(find "$HOME/.claude/plugins/marketplaces" -maxdepth 1 -name "cc-speak" -type d 2>/dev/null | head -1)
SETTINGS="$HOME/.claude/settings.json"
HOOK_SCRIPT="$PLUGIN_DIR/hooks/stop-speak.py"

chmod +x "$HOOK_SCRIPT" 2>/dev/null

python3 - "$SETTINGS" "$HOOK_SCRIPT" <<'PY'
import json, os, sys, tempfile

settings_path = sys.argv[1]
hook_script   = sys.argv[2]

# Create settings.json if missing
if not os.path.exists(settings_path):
    os.makedirs(os.path.dirname(settings_path), exist_ok=True)
    with open(settings_path, "w") as f:
        json.dump({}, f)

with open(settings_path) as f:
    settings = json.load(f)

if "hooks" not in settings or not isinstance(settings["hooks"], dict):
    settings["hooks"] = {}

hooks = settings["hooks"]

# Remove existing cc-speak entries (idempotent)
if "Stop" in hooks and isinstance(hooks["Stop"], list):
    cleaned = []
    for entry in hooks["Stop"]:
        if not isinstance(entry, dict):
            cleaned.append(entry)
            continue
        filtered = [
            h for h in entry.get("hooks", [])
            if "cc-speak" not in h.get("command", "")
            and "stop-speak" not in h.get("command", "")
        ]
        if filtered:
            cleaned.append({**entry, "hooks": filtered})
    hooks["Stop"] = cleaned

# Append new entry
hooks.setdefault("Stop", []).append({
    "hooks": [{
        "type": "command",
        "command": f"python3 {hook_script}",
        "timeout": 5000,
        "description": "cc-speak: read aloud last assistant message"
    }]
})

# Atomic write
dir_ = os.path.dirname(settings_path)
fd, tmp = tempfile.mkstemp(dir=dir_, suffix=".json.tmp")
try:
    with os.fdopen(fd, "w") as f:
        json.dump(settings, f, indent=2, ensure_ascii=False)
        f.write("\n")
    os.replace(tmp, settings_path)
    print("HOOK_REGISTERED")
except Exception as e:
    try: os.unlink(tmp)
    except: pass
    print(f"ERROR: {e}")
PY
```

If the output is `HOOK_REGISTERED`, proceed to Step 5.
If the output starts with `ERROR`, report it to the user and stop.

## Step 5 — Install default config

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

## Step 6 — Done

Tell the user:

> cc-speak is installed. **Restart Claude Code** for the hook to take effect.
>
> After restarting, Claude will read aloud the last message after each task.
>
> - Config: `~/.config/cc-speak/config.json`
> - Logs: `tail -f /tmp/cc-speak.log`
> - To uninstall: `/cc-speak:uninstall`
