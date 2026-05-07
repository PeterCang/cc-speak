---
name: off
description: "Disable cc-speak TTS. TRIGGERS - /cc-speak:off, turn off cc-speak, disable cc-speak, mute cc-speak."
allowed-tools: Bash
---

# cc-speak Off

Disable cc-speak by setting `enabled: false` in the config file.

```bash
python3 - <<'PY' 2>/dev/null || python - <<'PY'
import json, os, tempfile
config_path = os.path.expanduser("~/.config/cc-speak/config.json")
if not os.path.exists(config_path):
    print("CONFIG_NOT_FOUND")
    raise SystemExit(0)
with open(config_path) as f:
    cfg = json.load(f)
if not cfg.get("enabled", True):
    print("ALREADY_DISABLED")
    raise SystemExit(0)
cfg["enabled"] = False
dir_ = os.path.dirname(config_path)
fd, tmp = tempfile.mkstemp(dir=dir_, suffix=".json.tmp")
with os.fdopen(fd, "w") as f:
    json.dump(cfg, f, indent=2, ensure_ascii=False)
    f.write("\n")
os.replace(tmp, config_path)
print("DISABLED")
PY
```

- If output is `CONFIG_NOT_FOUND`: tell the user to run `/cc-speak:install` first.
- If output is `ALREADY_DISABLED`: tell the user cc-speak is already off.
- If output is `DISABLED`: tell the user cc-speak has been turned off. TTS will be silent until re-enabled with `/cc-speak:on`.
