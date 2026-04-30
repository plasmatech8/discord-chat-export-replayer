import json
import time
import requests
import os
from dotenv import load_dotenv

load_dotenv()

WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
JSON_FILE = os.getenv("EXPORT_JSON_FILE")
RE_UPLOAD_FILES = True
DELAY = 1.5
UPLOAD_LIMIT_MB = 10
# 9MB leaves room for multipart form data overhead under a 10MB upload limit.
MAX_FILE_SIZE = 9 * 1024 * 1024


def get_attachment_size_bytes(attachment, file_url):
    file_size = attachment.get('fileSizeBytes') or attachment.get('fileSize')
    if file_size:
        return file_size

    try:
        head_res = requests.head(file_url, allow_redirects=True, timeout=10)
        content_length = head_res.headers.get('Content-Length')
        if content_length:
            return int(content_length)
    except Exception:
        pass

    return None


def get_replay_content_and_attachments(message):
    content = (message.get('content') or '').strip()
    attachments = list(message.get('attachments') or [])

    reference = message.get('reference') or {}
    forwarded_message = message.get('forwardedMessage') or {}
    is_forward = reference.get('type') == 'Forward' and forwarded_message

    if not is_forward:
        return content, attachments

    forwarded_content = (forwarded_message.get('content') or '').strip()
    forwarded_attachments = list(forwarded_message.get('attachments') or [])

    if not attachments and forwarded_attachments:
        attachments = forwarded_attachments

    forward_header = '[Forwarded message]'
    if content and forwarded_content:
        combined_content = f"{content}\n\n{forward_header}\n{forwarded_content}"
    elif content:
        combined_content = f"{content}\n\n{forward_header}"
    elif forwarded_content:
        combined_content = f"{forward_header}\n{forwarded_content}"
    else:
        combined_content = forward_header

    return combined_content.strip(), attachments


def replay_messages():
    if not os.path.exists(JSON_FILE):
        print(f"Error: {JSON_FILE} not found.")
        return

    with open(JSON_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)

    messages = data.get('messages', [])
    print(f"Found {len(messages)} messages. Starting smart replay...")

    for msg in messages:
        author = msg.get('author', {})
        username = author.get('nickname') or author.get('name', 'Unknown User')
        avatar_url = author.get('avatarUrl')
        content, attachments = get_replay_content_and_attachments(msg)

        payload = {
            "username": username,
            "avatar_url": avatar_url,
            "content": content
        }

        files_to_upload = {}
        skipped_files = []
        total_upload_size = 0

        if RE_UPLOAD_FILES and attachments:
            for i, att in enumerate(attachments):
                file_url = att.get('url')
                file_name = att.get('fileName', f'file_{i}')
                file_size = get_attachment_size_bytes(att, file_url)

                if not file_url:
                    skipped_files.append(file_name)
                    continue

                if file_size and file_size > MAX_FILE_SIZE:
                    print(
                        f"Skipping {file_name} ({file_size / 1024 / 1024:.2f} MB) - Too large.")
                    skipped_files.append(file_name)
                    continue

                try:
                    file_res = requests.get(
                        file_url,
                        timeout=10,
                        headers={"Accept-Encoding": "identity"}
                    )
                    if file_res.status_code == 200:
                        file_bytes = file_res.content
                        actual_size = len(file_bytes)

                        if actual_size > MAX_FILE_SIZE:
                            print(
                                f"Skipping {file_name} ({actual_size / 1024 / 1024:.2f} MB) - Too large.")
                            skipped_files.append(file_name)
                            file_res.close()
                            continue

                        if total_upload_size + actual_size > MAX_FILE_SIZE:
                            print(
                                f"Skipping {file_name} ({actual_size / 1024 / 1024:.2f} MB) - Message attachments would exceed upload limit.")
                            skipped_files.append(file_name)
                            file_res.close()
                            continue

                        files_to_upload[f"file{i}"] = (file_name, file_bytes)
                        total_upload_size += actual_size
                    else:
                        print(
                            f"Failed to download {file_name}: HTTP {file_res.status_code}")
                        skipped_files.append(file_name)
                        file_res.close()
                except Exception as e:
                    print(f"Failed to download {file_name}: {e}")
                    skipped_files.append(file_name)

        # Add a note to the message if we skipped anything
        if skipped_files:
            warning = f"\n\n⚠️ *[System: {len(skipped_files)} attachment(s) skipped because they exceeded the configured {UPLOAD_LIMIT_MB}MB upload limit: {', '.join(skipped_files)}]*"
            payload["content"] = (payload["content"] + warning).strip()

        if not payload["content"] and not files_to_upload:
            print(f"Skipping empty message from {username}")
            time.sleep(DELAY)
            continue

        # Send to Webhook
        while True:
            # We use 'data' for the username/avatar and 'files' for the content/attachments
            # Discord handles Webhooks differently when files are involved
            try:
                if files_to_upload:
                    multipart_payload = {
                        "payload_json": json.dumps(payload)
                    }
                    response = requests.post(
                        WEBHOOK_URL, data=multipart_payload, files=files_to_upload)
                else:
                    response = requests.post(WEBHOOK_URL, json=payload)

                if response.status_code == 429:
                    retry_after = response.json().get('retry_after', 5)
                    print(f"Rate limited! Sleeping {retry_after}s...")
                    time.sleep(retry_after)
                    continue
                elif response.status_code in [200, 204]:
                    print(f"Sent: {username}")
                    break
                else:
                    print(f"Error {response.status_code}: {response.text}")
                    break
            except Exception as e:
                print(f"Request failed: {e}")
                break

        time.sleep(DELAY)

    print("Replay complete!")


if __name__ == "__main__":
    replay_messages()
