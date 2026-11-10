import os
import csv
import requests
from datetime import datetime, timedelta

def process_bot_messages():
    token = os.environ.get('TELEGRAM_TOKEN')
    chat_id = os.environ.get('CHAT_ID') # Your personal chat ID so it only responds to you
    csv_file = 'questions.csv'
    
    if not token:
        print("❌ Error: Token missing.")
        return

    # Fetch recent messages from Telegram
    url = f"https://api.telegram.org/bot{token}/getUpdates"
    response = requests.get(url).json()
    
    if not response.get("ok"):
        print("Failed to fetch updates.")
        return

    new_csv_rows = []
    
    # IST Timestamp helper
    now_ist = (datetime.utcnow() + timedelta(hours=5, minutes=30)).strftime('%Y-%m-%d %H:%M:%S')

    for update in response.get("result", []):
        msg = update.get("message", {})
        sender_id = str(msg.get("chat", {}).get("id"))
        text = msg.get("text", "").strip()

        # Optional Security Check: Only process messages sent by YOU
        if chat_id and sender_id != str(chat_id):
            continue

        # --- TASK 1: SAVE TO CSV ---
        if text.startswith("/save"):
            # Remove "/save " from the message text
            content_to_save = text.replace("/save", "").strip()
            if content_to_save:
                new_csv_rows.append([now_ist, content_to_save])
                send_reply(token, sender_id, f"✅ Saved to CSV: \"{content_to_save}\"")
            else:
                send_reply(token, sender_id, "⚠️ Please write something after /save.")

        # --- TASK 2: DO A DIFFERENT TASK ---
        elif text.startswith("/task"):
            # Put whatever custom Python logic you want here for your second task
            task_action = text.replace("/task", "").strip()
            print(f"Executing task: {task_action}")
            send_reply(token, sender_id, f"🚀 Task executed successfully for: {task_action}")

    # Save filtered messages to CSV if any new ones came in
    if new_csv_rows:
        file_exists = os.path.exists(csv_file)
        with open(csv_file, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(['Timestamp_IST', 'Saved_Message'])
            writer.writerows(new_csv_rows)
        print(f"Successfully appended {len(new_csv_rows)} row(s) to {csv_file}.")

def send_reply(token, recipient_id, text):
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": recipient_id, "text": text}
    requests.post(url, json=payload)

if __name__ == "__main__":
    process_bot_messages()
