---
name: on
description: "Enable cc-speak TTS. TRIGGERS - /cc-speak:on, turn on cc-speak, enable cc-speak, unmute cc-speak."
allowed-tools: Bash
---

# cc-speak On

Enable cc-speak by setting `enabled: true` in the config file.

```bash
python3 - <<'PY' 2>/dev/null || python - <<'PY'
import json, os, tempfile
config_path = os.path.expanduser("~/.config/cc-speak/config.json")
if not os.path.exists(config_path):
    print("CONFIG_NOT_FOUND")
    raise SystemExit(0)
with open(config_path) as f:
    cfg = json.load(f)
if cfg.get("enabled", True):
    print("ALREADY_ENABLED")
    raise SystemExit(0)
cfg["enabled"] = True
dir_ = os.path.dirname(config_path)
fd, tmp = tempfile.mkstemp(dir=dir_, suffix=".json.tmp")
with os.fdopen(fd, "w") as f:
    json.dump(cfg, f, indent=2, ensure_ascii=False)
    f.write("\n")
os.replace(tmp, config_path)
print("ENABLED")
PY
```

- If output is `CONFIG_NOT_FOUND`: tell the user to run `/cc-speak:install` first.
- If output is `ALREADY_ENABLED`: tell the user cc-speak is already on.
- If output is `ENABLED`: tell the user cc-speak has been turned on. TTS will resume from the next task.
