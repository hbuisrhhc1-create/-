cd /home/hbuisrhhc1111/bot1/
rm -f bot.py .bot.py.swp
cat << 'EOF' > bot.py
import warnings
warnings.filterwarnings("ignore")

import os
import string
import difflib
import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from duckduckgo_search import DDGS
from flask import Flask
import threading
import time

TELEGRAM_TOKEN = os.environ.get("TOKEN", "YOUR_BOT_TOKEN_HERE")
ADMIN_CHAT_ID_RAW = os.environ.get("ADMIN_CHAT_ID", "0")
ADMIN_CHAT_ID = int(ADMIN_CHAT_ID_RAW) if ADMIN_CHAT_ID_RAW.lstrip('-').isdigit() else 0

BUSINESS_NAME = "העסק שלי"
WELCOME_TEXT = "שלום רב וברוכים הבאים! 🛒\nנשמח לעמוד לשירותכם."
NOT_FOUND_MESSAGE = "מצטערים, לא מצאנו מענה לשאלה שלך. העברנו את הפנייה ישירות לצוות הניהול שלנו."

KNOWLEDGE_BASE = {}

bot = telebot.TeleBot(TELEGRAM_TOKEN) if TELEGRAM_TOKEN else None

pending_replies = {}
last_bot_messages = {}
last_user_questions = {}

def normalize_text(text):
    if not text:
        return ""
    text = text.strip()
    for p in string.punctuation + "؟،؛«»":
        text = text.replace(p, "")
    return " ".join(text.split())

def get_main_keyboard():
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    has_buttons = False
    for question in KNOWLEDGE_BASE.keys():
        if question.startswith("-"):
            markup.add(KeyboardButton(question))
            has_buttons = True
    if has_buttons:
        markup.add(KeyboardButton("📌 שאלות נפוצות"))
    return markup

def get_inline_questions_keyboard():
    markup = InlineKeyboardMarkup(row_width=1)
    for question in list(KNOWLEDGE_BASE.keys()):
        if question.startswith("-"):
            markup.add(InlineKeyboardButton(text=question, callback_data=f"ask_{question}"))
    return markup

def get_start_button_keyboard():
    markup = InlineKeyboardMarkup()
    if any(q.startswith("-") for q in KNOWLEDGE_BASE.keys()):
        markup.add(InlineKeyboardButton(text="🚀 התחל / Start", callback_data="start_bot"))
    return markup

def get_back_to_menu_keyboard():
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton(text="🔙 חזרה לתפריט הראשי", callback_data="back_to_menu"))
    return markup

@bot.message_handler(commands=['start', 'help', 'menu', 'popular'])
def send_welcome(message):
    markup_kb = get_start_button_keyboard()
    bot.send_message(
        message.chat.id, 
        WELCOME_TEXT, 
        reply_markup=markup_kb if markup_kb.keyboard else None
    )
    last_bot_messages[message.chat.id] = WELCOME_TEXT
    last_user_questions[message.chat.id] = "/start"

@bot.callback_query_handler(func=lambda call: True)
def handle_callbacks(call):
    try:
        bot.answer_callback_query(call.id)
    except Exception:
        pass

    if call.data == "start_bot":
        markup_inline = get_inline_questions_keyboard()
        text_to_send = f"📌 **תפריט ראשי - {BUSINESS_NAME}:**\nבחר שאלה מהרשימה:"
        try:
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=text_to_send, reply_markup=markup_inline, parse_mode="Markdown")
        except Exception:
            bot.send_message(call.message.chat.id, text_to_send, reply_markup=markup_inline, parse_mode="Markdown")
        last_bot_messages[call.message.chat.id] = text_to_send

    elif call.data == "back_to_menu":
        markup_inline = get_inline_questions_keyboard()
        text_to_send = "📌 **בחר שאלה נוספת מהרשימה:**"
        try:
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=text_to_send, reply_markup=markup_inline, parse_mode="Markdown")
        except Exception:
            bot.send_message(call.message.chat.id, text_to_send, reply_markup=markup_inline, parse_mode="Markdown")
        last_bot_messages[call.message.chat.id] = text_to_send

    elif call.data.startswith('ask_'):
        question_key = call.data.replace('ask_', '')
        if question_key in KNOWLEDGE_BASE:
            answer = KNOWLEDGE_BASE[question_key]
            text_to_send = f"📌 **{question_key}**\n\n{answer}"
            try:
                bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=text_to_send, reply_markup=get_back_to_menu_keyboard(), parse_mode="Markdown")
            except Exception:
                bot.send_message(call.message.chat.id, text_to_send, reply_markup=get_back_to_menu_keyboard(), parse_mode="Markdown")
            last_bot_messages[call.message.chat.id] = text_to_send
            last_user_questions[call.message.chat.id] = question_key

def search_the_web(query):
    try:
        focused_query = f"{query} {BUSINESS_NAME}"
        with DDGS() as ddgs:
            results = [r['body'] for r in ddgs.text(focused_query, max_results=3)]
            if results:
                combined_results = "\n\n".join(results)
                if any(w in combined_results for w in [w for w in query.split() if len(w) > 2]) or BUSINESS_NAME in combined_results:
                    return combined_results
    except Exception as e:
        print(f"Search error: {e}")
    return None

@bot.message_handler(content_types=['document'])
def handle_docs(message):
    global BUSINESS_NAME, WELCOME_TEXT
    if message.chat.id != ADMIN_CHAT_ID:
        return
    
    try:
        file_info = bot.get_file(message.document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        file_content = downloaded_file.decode('utf-8')
        added_count = 0
        
        for line in file_content.splitlines():
            if "|" in line:
                parts = line.split("|", 1)
                key = parts[0].strip()
                val = parts[1].strip()
                
                if key.upper() == "NAME":
                    BUSINESS_NAME = val
                elif key.upper() == "WELCOME":
                    WELCOME_TEXT = val
                elif key and val:
                    KNOWLEDGE_BASE[key] = val
                    added_count += 1
                    
        bot.reply_to(message, f"📁 הקובץ נקלט בהצלחה!\nשם העסק הנוכחי: {BUSINESS_NAME}\nסך הכל שאלות במאגר: {len(KNOWLEDGE_BASE)}\nנוספו/עודכנו {added_count} פריטים.")
    except Exception as e:
        bot.reply_to(message, f"❌ שגיאה בקריאת הקובץ: {e}")

@bot.message_handler(func=lambda message: message.chat.id == ADMIN_CHAT_ID)
def handle_admin_messages(message):
    user_text = message.text or message.caption or ""

    if message.reply_to_message:
        replied_msg_id = message.reply_to_message.message_id
        if replied_msg_id in pending_replies:
            target_user_chat_id = pending_replies[replied_msg_id]
            admin_answer = user_text.strip()
            try:
                bot.send_message(target_user_chat_id, f"💬 תשובה מהצוות:\n\n{admin_answer}")
                bot.reply_to(message, "✅ התשובה נשלחה ללקוח בהצלחה!")
            except Exception as e:
                bot.reply_to(message, f"❌ שגיאה בשליחת התשובה ללקוח: {e}")
            return

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    if message.chat.id == ADMIN_CHAT_ID:
        return

    user_text = message.text.strip() if message.text else ""
    markup = get_main_keyboard()
    normalized_knowledge_base = {normalize_text(k): v for k, v in KNOWLEDGE_BASE.items()}
    lower_user_text = user_text.lower()
    chat_id = message.chat.id

    forward_triggers = ["תגיד לצוות", "תאמר לצוות", "תגיד למנהל", "תאמר למנהל"]
    if any(lower_user_text.startswith(trigger) for trigger in forward_triggers):
        bot.reply_to(message, "הבקשה שלך הועברה ישירות לצוות הניהול.", reply_markup=markup)
        if ADMIN_CHAT_ID:
            try:
                user_handle = f"@{message.from_user.username}" if message.from_user.username else "אין שם משתמש"
                prev_q = last_user_questions.get(chat_id, "לא ידוע")
                prev_a = last_bot_messages.get(chat_id, "אין תיעוד")
                alert_text = (
                    f"📨 **הודעה ייעודית לצוות משתמש!**\n"
                    f"👤 שם: {message.from_user.first_name}\n"
                    f"🔗 טג: {user_handle}\n"
                    f"🆔 מזהה: `{chat_id}`\n"
                    f"❓ שאלה אחרונה: {prev_q}\n"
                    f"🤖 תשובה אחרונה: {prev_a}\n"
                    f"💬 תוכן ההודעה: {user_text}"
                )
                sent_alert = bot.send_message(ADMIN_CHAT_ID, alert_text, parse_mode="Markdown")
                pending_replies[sent_alert.message_id] = chat_id
            except Exception as e:
                print(f"Error: {e}")
        return

    error_triggers = ["יש טעות", "טעות", "תעות", "לא נכון", "שגוי", "שגיה", "זה לא נכון", "יש תקלה", "בעיה"]
    if any(trigger in lower_user_text for trigger in error_triggers):
        bot.reply_to(message, "תודה על העדכון! העברתי את הדיווח לצוות הניהול לבדיקה.", reply_markup=markup)
        if ADMIN_CHAT_ID:
            try:
                user_handle = f"@{message.from_user.username}" if message.from_user.username else "אין שם משתמש"
                prev_q = last_user_questions.get(chat_id, "לא ידוע")
                prev_a = last_bot_messages.get(chat_id, "אין תיעוד")
                alert_text = (
                    f"⚠️ **דיווח על טעות/תקלה!**\n"
                    f"👤 שם: {message.from_user.first_name}\n"
                    f"🔗 טג: {user_handle}\n"
                    f"🆔 מזהה: `{chat_id}`\n"
                    f"❓ שאלה: {prev_q}\n"
                    f"🤖 תשובה: {prev_a}\n"
                    f"💬 דיווח: {user_text}"
                )
                sent_alert = bot.send_message(ADMIN_CHAT_ID, alert_text, parse_mode="Markdown")
                pending_replies[sent_alert.message_id] = chat_id
            except Exception as e:
                print(f"Error: {e}")
        return

    if user_text == "📌 שאלות נפוצות":
        popular_questions = [q for q in KNOWLEDGE_BASE.keys() if q.startswith("-")]
        popular_text = f"📌 **השאלות הנפוצות ביותר ב-{BUSINESS_NAME}:**\n\n" + "\n".join([f"• {q}" for q in popular_questions])
        markup_inline = get_inline_questions_keyboard()
        sent = bot.reply_to(message, popular_text, reply_markup=markup_inline)
        last_bot_messages[chat_id] = popular_text
        last_user_questions[chat_id] = "📌 שאלות נפוצות"
        return

    if any(g in lower_user_text for g in ["שלום", "היי", "הלו", "מה נשמע", "בוקר טוב", "ערב טוב"]):
        greet_markup = get_start_button_keyboard()
        greet_text = f"שלום רב ל-{BUSINESS_NAME}! " + ("לחץ על כפתור ההתחלה כדי לפתוח את התפריט:" if greet_markup.keyboard else "כיצד נוכל לעזור לך היום?")
        sent = bot.reply_to(message, greet_text, reply_markup=greet_markup if greet_markup.keyboard else markup)
        last_bot_messages[chat_id] = greet_text
        last_user_questions[chat_id] = user_text
        return

    clean_user_text = normalize_text(user_text)
    matched_key = None
    if clean_user_text in normalized_knowledge_base:
        matched_key = clean_user_text
    else:
        close_matches = difflib.get_close_matches(clean_user_text, list(normalized_knowledge_base.keys()), n=1, cutoff=0.7)
        if close_matches:
            matched_key = close_matches[0]

    if matched_key:
        original_key = [k for k in KNOWLEDGE_BASE.keys() if normalize_text(k) == matched_key][0]
        answer = KNOWLEDGE_BASE[original_key]
        bot.send_chat_action(chat_id, 'typing')
        sent = bot.reply_to(message, answer, reply_markup=markup)
        last_bot_messages[chat_id] = answer
        last_user_questions[chat_id] = original_key
    else:
        bot.send_chat_action(chat_id, 'typing')
        web_result = search_the_web(user_text)
        if web_result:
            reply_to_send = f"מצאתי את המידע הבא:\n\n{web_result}"
            bot.reply_to(message, reply_to_send, reply_markup=markup)
            last_bot_messages[chat_id] = reply_to_send
            last_user_questions[chat_id] = user_text
        else:
            bot.reply_to(message, NOT_FOUND_MESSAGE, reply_markup=markup)
            last_bot_messages[chat_id] = NOT_FOUND_MESSAGE
            last_user_questions[chat_id] = user_text
            
        if ADMIN_CHAT_ID:
            try:
                user_handle = f"@{message.from_user.username}" if message.from_user.username else "אין שם משתמש"
                prev_a = last_bot_messages.get(chat_id, NOT_FOUND_MESSAGE)
                sent_alert = bot.send_message(
                    ADMIN_CHAT_ID, 
                    f"❓ **שאלה חדשה שלא נמצאה:**\n"
                    f"👤 שם: {message.from_user.first_name}\n"
                    f"🔗 טג: {user_handle}\n"
                    f"🆔 מזהה: `{chat_id}`\n"
                    f"🤖 התשובה האחרונה: {prev_a}\n"
                    f"תוכן הודעת המשתמש: {user_text}",
                    parse_mode="Markdown"
                )
                pending_replies[sent_alert.message_id] = chat_id
            except Exception as e:
                print(f"Error: {e}")

def weekly_admin_reminder():
    reminder_text = (
        "⏰ **תזכורת שבועית לניהול הבוט:**\n\n"
        "כדי לעדכן את פרטי העסק, שם הבוט או להוסיף שאלות ותשובות חדשות, כל מה שצריך לעשות הוא **לשלוח לכאן קובץ טקסט (.txt)** במבנה הבא:\n\n"
        "• `NAME|שם העסק החדש` (לעדכון שם הבוט)\n"
        "• `WELCOME|הודעת פתיחה חדשה` (לעדכון הודעת הפתיחה)\n"
        "• `-שאלה שתוצג ככפתור?|התשובה עליה`\n"
        "• `שאלה רגילה בלי כפתור?|התשובה עליה`\n\n"
        "הבוט יקלוט את הקובץ אוטומטית ויעדכן את הנתונים מיד!"
    )
    while True:
        if ADMIN_CHAT_ID != 0 and bot:
            try:
                bot.send_message(ADMIN_CHAT_ID, reminder_text, parse_mode="Markdown")
            except Exception as e:
                print(f"Reminder error: {e}")
        time.sleep(7 * 24 * 60 * 60)

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running successfully!", 200

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

if __name__ == "__main__":
    t = threading.Thread(target=run_flask)
    t.start()
    
    reminder_thread = threading.Thread(target=weekly_admin_reminder, daemon=True)
    reminder_thread.start()
    
    if bot:
        print("Single-file Bot Engine is running successfully...")
        bot.infinity_polling(allowed_updates=['message', 'edited_message', 'callback_query'])
    else:
        print("Error: TELEGRAM_TOKEN is missing!")
EOF
