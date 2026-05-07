---
name: uninstall
description: "Uninstall cc-speak: removes config and any legacy hook entries, then guides the user to remove the plugin. TRIGGERS - /cc-speak:uninstall, uninstall cc-speak, remove cc-speak."
allowed-tools: Bash
---

# cc-speak Uninstall

Remove cc-speak config and any legacy hook entries from `settings.json`, then
instruct the user to remove the plugin package.

## Step 1 — Remove legacy settings.json hook entries

```bash
python3 - <<'PY' 2>/dev/null || python - <<'PY'
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

- `SETTINGS_NOT_FOUND` or `NO_LEGACY_ENTRIES`: nothing to clean up, continue.
- `REMOVED_N_LEGACY_ENTRIES`: legacy entries removed, continue.

## Step 2 — Remove config file and directory

```bash
python3 - <<'PY' 2>/dev/null || python - <<'PY'
import os, shutil
config_path = os.path.expanduser("~/.config/cc-speak/config.json")
config_dir  = os.path.expanduser("~/.config/cc-speak")
if not os.path.exists(config_path):
    print("CONFIG_NOT_FOUND")
    raise SystemExit(0)
os.remove(config_path)
try:
    os.rmdir(config_dir)   # only removes if empty
    print("CONFIG_AND_DIR_REMOVED")
except OSError:
    print("CONFIG_REMOVED")
PY
```

- `CONFIG_NOT_FOUND`: config was never created, continue.
- `CONFIG_REMOVED`: config file deleted (directory kept because it had other files).
- `CONFIG_AND_DIR_REMOVED`: config file and directory both deleted.

## Step 3 — Done

Tell the user:

> cc-speak config and hook entries have been removed.
>
> To finish uninstalling, run this command in your terminal:
>
> ```bash
> claude plugin uninstall cc-speak@cc-speak --scope user
> ```
>
> Then restart Claude Code. TTS will no longer run after tasks.
