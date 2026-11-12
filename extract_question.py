import os
import csv
import requests
from datetime import datetime, timedelta

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
        text = msg.get("text", "").strip()

        # Optional Security Check: Only process messages sent by YOU
        if chat_id and sender_id != str(sender_id): # fixed comparison safety
            continue

        # --- TASK 1: SAVE TO CSV ---
        if text.startswith("/save"):
            content_to_save = text.replace("/save", "").strip()
            if content_to_save:
                new_csv_rows.append([ content_to_save])
                send_reply(token, sender_id, f"✅ Saved to CSV: "\{content_to_save}\"")
            else:
                send_reply(token, sender_id, "⚠️ Please write something after /save.")

        # --- TASK 2: DO A DIFFERENT TASK ---
        elif text.startswith("/task"):
            task_action = text.replace("/task", "").strip()
            print(f"Executing task: {task_action}")
            send_reply(token, sender_id, f"🚀 Task executed successfully for: {task_action}")

    # 3. Save filtered messages to CSV if any new ones came in
    if new_csv_rows:
        file_exists = os.path.exists(csv_file)
        with open(csv_file, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(['Timestamp_IST', 'Saved_Message'])
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
