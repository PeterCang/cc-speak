# cc-speak

A Claude Code plugin that reads aloud the last assistant message after each task completes, using [edge-tts](https://github.com/rany2/edge-tts) (Microsoft neural TTS).

## Install

```bash
# 1. Add the marketplace
claude plugin marketplace add PeterCang/cc-speak

# 2. Install the plugin
claude plugin install cc-speak@cc-speak --scope user

# 3. Inside Claude Code, run the install skill
/cc-speak:install
```

The install skill automatically checks for `edge-tts` and installs it if missing, then registers the Stop hook.

Restart Claude Code after install. That's it — Claude will read aloud after every task.

## Uninstall

Inside Claude Code, run the uninstall skill first — it removes the config file
and any legacy hook entries from `settings.json`:

```
/cc-speak:uninstall
```

Then remove the plugin package from your terminal:

```bash
claude plugin uninstall cc-speak@cc-speak --scope user
```

Restart Claude Code. TTS will no longer run after tasks.

## Update

```bash
claude plugin marketplace update cc-speak
claude plugin update cc-speak@cc-speak --scope user
```

The hook runs from the marketplace clone (`~/.claude/plugins/marketplaces/cc-speak/`), so updates take effect immediately without restarting Claude Code.

## Toggle TTS on/off

You can mute and unmute cc-speak at any time without uninstalling it.

Inside Claude Code:

```
/cc-speak:off   # stop reading aloud
/cc-speak:on    # resume reading aloud
```

This sets `enabled` in `~/.config/cc-speak/config.json` and takes effect from the next task — no restart needed.

## Configuration

Edit `~/.config/cc-speak/config.json`:

```json
{
  "enabled": true,
  "edge_voice_zh": "zh-CN-YunxiNeural",
  "edge_voice_en": "en-US-JennyNeural",
  "max_chars": 300,
  "min_chars": 5,
  "log_file": "/tmp/cc-speak.log"
}
```

| Field | Default | Description |
|-------|---------|-------------|
| `enabled` | `true` | Set to `false` to mute without uninstalling |
| `edge_voice_zh` | `zh-CN-YunxiNeural` | Voice for Chinese text |
| `edge_voice_en` | `en-US-JennyNeural` | Voice for English text |
| `max_chars` | `300` | Max characters to speak (truncates at sentence boundary) |
| `min_chars` | `5` | Skip responses shorter than this |
| `log_file` | `/tmp/cc-speak.log` | Log path, or `""` to disable |

List available voices: `edge-tts --list-voices`

## How it works

cc-speak registers a `Stop` hook. When Claude Code finishes a task:

1. Reads the session transcript (JSONL)
2. Finds the last assistant message with text content (skips tool-use-only turns)
3. Strips Markdown and truncates to `max_chars`
4. Detects language (Chinese vs English) and picks the matching voice
5. Launches edge-tts in a detached background process — Claude Code is never blocked

## Debugging

Log path varies by platform:

- **Windows**: `%LOCALAPPDATA%\Temp\cc-speak.log`
- **macOS / Linux**: `/tmp/cc-speak.log`

Tail the log to watch what cc-speak is doing:

```bash
# macOS / Linux
tail -f /tmp/cc-speak.log

# Windows (PowerShell)
Get-Content "$env:LOCALAPPDATA\Temp\cc-speak.log" -Wait
```

The log path can be changed or disabled (`""`) via the `log_file` field in the config.

## Requirements

- Python 3.6+
- `edge-tts` (auto-installed by `/cc-speak:install`)
- macOS: `afplay` (built-in) / Linux: `aplay` / Windows: PowerShell `SoundPlayer` (built-in)

## Supported Platforms

| Platform | Status |
|----------|--------|
| macOS | Tested ✓ |
| Windows | Tested ✓ |
| Linux | Should work (requires `aplay`) |

## License

MIT
