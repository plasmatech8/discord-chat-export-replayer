## Discord Text Channel Replayer

Replay messages from a Discord chat export into another text channel through a webhook.

This script reads a JSON export produced by DiscordChatExporter and recreates the message history in another Discord text channel while preserving:

- display name
- avatar
- message content
- supported attachments
- forwarded message content

## Requirements

- Python 3.10+
- A Discord webhook URL for the destination channel
- A chat export in JSON format from DiscordChatExporter

## 1. Export the source channel

1. Download DiscordChatExporter from https://github.com/Tyrrrz/DiscordChatExporter/releases
2. Open `DiscordChatExporter.exe`
3. Export the source channel as `JSON`
4. Keep the exported file somewhere accessible to this project

## 2. Install dependencies

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

If you already use another Python environment, install the same requirements there instead.

## 3. Configure environment variables

Create a local `.env` file from `.env.example` and fill in your values:

```env
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...
EXPORT_JSON_FILE=clips.json
```

Variable meanings:

- `DISCORD_WEBHOOK_URL`: webhook for the destination channel
- `EXPORT_JSON_FILE`: path to the exported DiscordChatExporter JSON file

## 4. Run the replay

```bash
python replay_discord.py
```

The script will print progress in the terminal as it sends messages.

## Notes

- Attachments are re-uploaded when possible.
- Files larger than the configured safe upload limit are skipped and noted in the replayed message.
- The current safety cap is tuned for a 10 MB webhook upload limit.
- Empty messages with no uploadable attachments are skipped.
