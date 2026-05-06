# cc-speak Development Rules

## Before pushing to GitHub

**Always bump the version number before committing and pushing.**

Version is tracked in two files — both must be updated together:
- `.claude-plugin/plugin.json` → `"version"` field
- `.claude-plugin/marketplace.json` → `"version"` field inside `plugins[0]`

Follow semver patch increments (e.g. 1.0.5 → 1.0.6) for bug fixes, minor increments for new features.
