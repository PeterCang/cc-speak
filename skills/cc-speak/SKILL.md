---
name: install
description: "Install cc-speak: checks for edge-tts, installs it if missing, then sets up the default config. TRIGGERS - /cc-speak:install, install cc-speak, setup cc-speak."
allowed-tools: Bash, Read, Write, Edit
---

# cc-speak Install

Sets up cc-speak so Claude Code reads aloud the last assistant message after
each task completes. The Stop hook is auto-loaded from `hooks/hooks.json` by
the Claude Code plugin system — no `settings.json` registration needed.

## Step 1 — Detect Python

Find the Python 3 command available on this machine:

```bash
PYTHON_CMD=""
for cmd in python3 python py; do
  if command -v "$cmd" >/dev/null 2>&1; then
    PY_MAJOR=$("$cmd" -c "import sys; print(sys.version_info.major)" 2>/dev/null)
    if [ "$PY_MAJOR" = "3" ]; then
      PYTHON_CMD="$cmd"
      echo "PYTHON_FOUND: $cmd ($("$cmd" --version 2>&1))"
      break
    fi
  fi
done
if [ -z "$PYTHON_CMD" ]; then
  echo "PYTHON_NOT_FOUND"
fi
```

If the output is `PYTHON_NOT_FOUND`, tell the user Python 3 is required and stop.

Save the detected command (e.g. `python3`, `python`, or `py`) — it will be used in Step 5 to patch the hook command.

## Step 2 — Check and install edge-tts

```bash
"$PYTHON_CMD" -c "import edge_tts; print('edge-tts OK')" 2>/dev/null || echo "EDGE_TTS_MISSING"
```

If the output is `EDGE_TTS_MISSING`, install it now:

```bash
"$PYTHON_CMD" -m pip install edge-tts --break-system-packages 2>&1 | grep -v "^note\|^hint\|^warning" || \
"$PYTHON_CMD" -m pip install edge-tts 2>&1 | tail -3
"$PYTHON_CMD" -c "import edge_tts; print('edge-tts installed OK')" 2>/dev/null || echo "INSTALL_FAILED"
```

If the output is `INSTALL_FAILED`, tell the user to run `python3 -m pip install edge-tts --break-system-packages` manually and stop.

## Step 3 — Verify hook script is executable

```bash
PLUGIN_DIR=$(find "$HOME/.claude/plugins/marketplaces" -maxdepth 1 -name "cc-speak" -type d 2>/dev/null | head -1)
if [ -z "$PLUGIN_DIR" ]; then
  echo "NOT_FOUND"
else
  chmod +x "$PLUGIN_DIR/hooks/stop-speak.py" "$PLUGIN_DIR/hooks/run.sh" 2>/dev/null
  echo "HOOK_READY: $PLUGIN_DIR"
fi
```

If the output is `NOT_FOUND`, tell the user to run `claude plugin marketplace add PeterCang/cc-speak` first and stop.

## Step 4 — Patch hooks.json with the detected Python command

The installed `hooks.json` may still reference `python3` which can be a broken Store alias on Windows. Replace it with the `PYTHON_CMD` detected in Step 1:

```bash
PLUGIN_DIR=$(find "$HOME/.claude/plugins/marketplaces" -maxdepth 1 -name "cc-speak" -type d 2>/dev/null | head -1)
HOOKS_JSON="$PLUGIN_DIR/hooks/hooks.json"
if [ -f "$HOOKS_JSON" ]; then
  "$PYTHON_CMD" - <<PY
import json, os, tempfile
hooks_path = os.path.expandvars("$HOOKS_JSON")
python_cmd = "$PYTHON_CMD"
with open(hooks_path) as f:
    data = json.load(f)
for group in data.get("hooks", {}).get("Stop", []):
    for hook in group.get("hooks", []):
        if "command" in hook:
            cmd = hook["command"]
            # Replace any python3/python/py prefix with the detected command
            import re
            hook["command"] = re.sub(
                r'^(python3|python|py)\b',
                python_cmd,
                cmd
            )
            # Also fix the fallback part after ||
            hook["command"] = re.sub(
                r'\|\|\s*(python3|python|py)\b',
                '|| ' + python_cmd,
                hook["command"]
            )
fd, tmp = tempfile.mkstemp(dir=os.path.dirname(hooks_path), suffix=".json.tmp")
with os.fdopen(fd, "w") as f:
    json.dump(data, f, indent=2)
    f.write("\n")
os.replace(tmp, hooks_path)
print("HOOKS_PATCHED: " + python_cmd)
PY
else
  echo "HOOKS_JSON_NOT_FOUND"
fi
```

## Step 5 — Remove any legacy settings.json entries (prevent double-firing)

The hook is auto-loaded from `hooks/hooks.json`. Any old cc-speak entries in `settings.json` from a previous install will cause the hook to fire twice. Remove them:

```bash
"$PYTHON_CMD" - <<'PY' 2>/dev/null || echo "CLEANUP_SKIPPED"
import json, os, tempfile
settings_path = os.path.expanduser("~/.claude/settings.json")
if not os.path.exists(settings_path):
    print("SETTINGS_NOT_FOUND")
    raise SystemExit(0)
with open(settings_path) as f:
    settings = json.load(f)
hooks = settings.get("hooks", {})
removed = 0
if "Stop" in hooks and isinstance(hooks["Stop"], list):
    cleaned = []
    for entry in hooks["Stop"]:
        if not isinstance(entry, dict):
            cleaned.append(entry); continue
        filtered = [h for h in entry.get("hooks", [])
                    if "cc-speak" not in h.get("command", "")
                    and "stop-speak" not in h.get("command", "")]
        removed += len(entry.get("hooks", [])) - len(filtered)
        if filtered:
            cleaned.append({**entry, "hooks": filtered})
    hooks["Stop"] = cleaned
if removed == 0:
    print("NO_LEGACY_ENTRIES")
    raise SystemExit(0)
dir_ = os.path.dirname(settings_path)
fd, tmp = tempfile.mkstemp(dir=dir_, suffix=".json.tmp")
with os.fdopen(fd, "w") as f:
    json.dump(settings, f, indent=2, ensure_ascii=False); f.write("\n")
os.replace(tmp, settings_path)
print(f"REMOVED_{removed}_LEGACY_ENTRIES")
PY
```

## Step 6 — Install default config

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

## Step 7 — Done

Tell the user:

> cc-speak is installed. **Restart Claude Code** for the hook to take effect.
>
> After restarting, Claude will read aloud the last message after each task.
>
> - Config: `~/.config/cc-speak/config.json`
> - Logs: `tail -f /tmp/cc-speak.log`
