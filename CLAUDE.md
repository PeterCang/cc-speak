# cc-speak Development Rules

## Before pushing to GitHub

**Always bump the version number before committing and pushing.**

Version is tracked in two files — both must be updated together:
- `.claude-plugin/plugin.json` → `"version"` field
- `.claude-plugin/marketplace.json` → `"version"` field inside `plugins[0]`

Follow semver patch increments (e.g. 1.0.5 → 1.0.6) for bug fixes, minor increments for new features.

## Changing default voices

When changing a default voice (e.g. `edge_voice_zh`), add the old default value to the corresponding set in `_LEGACY_DEFAULTS` in `hooks/stop-speak.py`. This ensures existing users whose config still holds the old default are silently migrated to the new one, without affecting users who manually customised their voice.

Example: changing `edge_voice_zh` from `zh-CN-XiaoxiaoNeural` to `zh-CN-YunxiNeural`:
```python
_LEGACY_DEFAULTS = {
    "edge_voice_zh": {"zh-CN-XiaoxiaoNeural"},  # add old default here
}
```
