# Discord Chat Export Replayer

Migrate messages from one Discord text channel to another, whether the destination is in the same server or a different server.

This project documents a simple workflow:

1. export a source channel with DiscordChatExporter
2. point the script at that export
3. replay the messages into a destination channel through a Discord webhook

The replay keeps the conversation recognizable by preserving:

- display names
- avatars
- message content
- supported attachments
- forwarded message content

## Before you start

You will need:

- Python 3.10+
- Access to the source channel you want to export
- Access to the destination channel where messages should be replayed
- Permission to create or manage webhooks in the destination channel

The export file and webhook URL are created during the setup steps below, so they do not need to exist ahead of time.

## Setup

### 1. Export the source channel

1. Download DiscordChatExporter from https://github.com/Tyrrrz/DiscordChatExporter/releases
2. Run `DiscordChatExporter.exe`
3. Find the Discord server that contains the text channel you want to copy
4. In that server, select the source text channel you want to export
5. Export that text channel as `JSON`
6. Keep the exported file somewhere accessible to this project

### 2. Create a webhook for the destination channel

1. Open the destination text channel in Discord
2. Open the channel settings for that channel
3. Go to `Integrations`
4. Open `Webhooks`
5. Create a new webhook
6. Optionally set the webhook name and avatar
7. Click `Copy Webhook URL`

That copied URL is the value you will use for `DISCORD_WEBHOOK_URL` in your `.env` file.

### 3. Install dependencies

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

If you already use another Python environment, install the same packages there instead.

### 4. Configure environment variables

Create a local `.env` file from `.env.example`, then fill in your values:

```env
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...
EXPORT_JSON_FILE=clips.json
```

Variables:

- `DISCORD_WEBHOOK_URL`: webhook URL for the destination channel
- `EXPORT_JSON_FILE`: path to the exported DiscordChatExporter JSON file

### 5. Run the replay

```bash
python replay_discord.py
```

The script prints progress in the terminal as each message is processed and sent.

## What to expect

The replayed messages look close to the original conversation, but they are posted by a webhook, so Discord shows an `APP` badge next to the displayed username.

If an attachment is too large to upload safely, the script skips it and adds a warning to the replayed message. Example:

```text
⚠️ [System: 1 attachment(s) skipped because they exceeded the configured 10MB upload limit: Team_Fortress2-_2026-04-11_7-36-21_PM.mp4]
```

## Notes

- Attachments are re-uploaded when possible.
- Files larger than the configured safe upload limit are skipped and noted in the replayed message.
- The current safety cap is tuned for a 10 MB webhook upload limit.
- Empty messages with no uploadable attachments are skipped.
