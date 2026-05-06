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

## Configuration

Edit `~/.config/cc-speak/config.json`:

```json
{
  "enabled": true,
  "edge_voice_zh": "zh-CN-XiaoxiaoNeural",
  "edge_voice_en": "en-US-JennyNeural",
  "max_chars": 300,
  "min_chars": 5,
  "log_file": "/tmp/cc-speak.log"
}
```

| Field | Default | Description |
|-------|---------|-------------|
| `enabled` | `true` | Set to `false` to mute without uninstalling |
| `edge_voice_zh` | `zh-CN-XiaoxiaoNeural` | Voice for Chinese text |
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

```bash
tail -f /tmp/cc-speak.log
```

## Requirements

- Python 3.6+
- `edge-tts` (auto-installed by `/cc-speak:install`)
- macOS: `afplay` (built-in) / Linux: `aplay`

## License

MIT
