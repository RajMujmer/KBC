import os
import csv
import requests
from datetime import datetime, timedelta

# Columns the quiz game expects in questions.csv (exactly these 7)
HEADER = ["level", "question", "option_a", "option_b", "option_c", "option_d", "answer"]
USAGE = ("⚠️ Format: /save level,question,A,B,C,D,answer\n"
         "Example: /save 5,What does G stand for in GUI?,Graphical,Graph,Green,Grave,A")


def parse_save(content):
    """Turn 'level,question,A,B,C,D,answer' into a clean 7-column row, or None if invalid."""
    content = content.replace('"', '')                      # remove " symbol
    parts = [" ".join(p.split()) for p in content.split(",")]   # also removes \n, \r, extra spaces
    if len(parts) < 7:
        return None
    level, answer = parts[0], parts[-1].upper()             # 'a' becomes 'A'
    opts = parts[-5:-1]
    question = ", ".join(parts[1:-5])                       # commas inside the question are kept
    if not (level.isdigit() and 1 <= int(level) <= 15 and question
            and all(opts) and answer in ("A", "B", "C", "D")):
        return None
    return [int(level), question, *opts, answer]


def process_bot_messages():
    token = os.environ.get('TELEGRAM_TOKEN')
    chat_id = os.environ.get('CHAT_ID') # Your personal chat ID so it only responds to you
    csv_file = 'questions.csv'
    offset_file = 'last_offset.txt'
    
    if not token:
        print("❌ Error: Token missing.")
        return

    # 1. Read the last processed update ID (the bookmark)
    last_update_id = 0
    if os.path.exists(offset_file):
        try:
            with open(offset_file, 'r') as f:
                last_update_id = int(f.read().strip())
        except ValueError:
            last_update_id = 0

    # 2. Pass offset to getUpdates (we want updates AFTER the last processed one)
    url = f"https://api.telegram.org/bot{token}/getUpdates"
    params = {"offset": last_update_id + 1} if last_update_id > 0 else {}
    
    response = requests.get(url, params=params).json()
    
    if not response.get("ok"):
        print("Failed to fetch updates.")
        return

    results = response.get("result", [])
    if not results:
        print("No new messages found.")
        return

    new_csv_rows = []
    highest_update_id = last_update_id
    
    # IST Timestamp helper
    now_ist = (datetime.utcnow() + timedelta(hours=5, minutes=30)).strftime('%Y-%m-%d %H:%M:%S')

    for update in results:
        update_id = update.get("update_id")
        if update_id > highest_update_id:
            highest_update_id = update_id

        msg = update.get("message", {})
        sender_id = str(msg.get("chat", {}).get("id"))
        text = (msg.get("text") or "").strip()

        # Security Check: Only process messages sent by YOU
        # (fixed: it used to compare sender_id with itself, so it never skipped anyone)
        if chat_id and sender_id != str(chat_id):
            continue

        # --- TASK 1: SAVE TO CSV ---
        if text == "/save" or text.startswith("/save "):
            content_to_save = text[len("/save"):].strip()
            row = parse_save(content_to_save) if content_to_save else None
            if row:
                new_csv_rows.append(row)
                send_reply(token, sender_id, f"✅ Saved: {row[1]}")
            else:
                send_reply(token, sender_id, USAGE)

        # --- TASK 2: DO A DIFFERENT TASK ---
        elif text.startswith("/task"):
            task_action = text.replace("/task", "").strip()
            print(f"Executing task: {task_action}")
            send_reply(token, sender_id, f"🚀 Task executed successfully for: {task_action}")

    # 3. Save filtered messages to CSV if any new ones came in
    if new_csv_rows:
        file_exists = os.path.exists(csv_file) and os.path.getsize(csv_file) > 0
        with open(csv_file, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)   # normal writer: quotes only when a question itself has a comma
            if not file_exists:
                writer.writerow(HEADER)
            writer.writerows(new_csv_rows)
        print(f"Successfully appended {len(new_csv_rows)} row(s) to {csv_file}.")

    # 4. Save the new bookmark position so we don't re-read these messages next time
    with open(offset_file, 'w') as f:
        f.write(str(highest_update_id))
    print(f"Updated offset bookmark to: {highest_update_id}")

def send_reply(token, recipient_id, text):
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": recipient_id, "text": text}
    requests.post(url, json=payload)

if __name__ == "__main__":
    process_bot_messages()
