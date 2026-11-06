import os
import requests
import threading
from flask import Flask

# Токен вашего бота и ID администратора
TOKEN = "9200361744:AAGZd7cuSCgdm3Cw2tpU3QKqQbGNJennAvU"
ADMIN_CHAT_ID = "7050276939"  # Замените при необходимости на ваш ID в Telegram

BASE_URL = f"https://api.telegram.org/bot{TOKEN}"

# --- НАСТРОЙКИ САЛОНА ---
SERVICES = {
    "1": {"name": "Женская стрижка", "price": "500 грн"},
    "2": {"name": "Маникюр", "price": "400 грн"},
    "3": {"name": "Окрашивание волос", "price": "1200 грн"},
    "4": {"name": "Коррекция бровей", "price": "250 грн"}
}

MASTERS = {
    "1": "Анна (Топ-мастер)",
    "2": "Катерина (Маникюр/Педикюр)",
    "3": "Мария (Бровист)",
    "4": "Елена (Парикмахер-стилист)"
}

user_data = {}

# --- ВЕБ-СЕРВЕР ДЛЯ RENDER ---
app = Flask('')

@app.route('/')
def home():
    return "BeautyFlow Bot is running 24/7!"


# --- ФУНКЦИИ TELEGRAM API ---
def send_message(chat_id, text, reply_markup=None):
    url = f"{BASE_URL}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
    if reply_markup:
        payload["reply_markup"] = reply_markup
    requests.post(url, json=payload)

def save_booking(booking_info):
    with open("bookings.txt", "a", encoding="utf-8") as f:
        f.write(booking_info + "\n")


# --- ОБРАБОТКА СООБЩЕНИЙ ---
def handle_update(update):
    if "message" in update:
        msg = update["message"]
        chat_id = msg["chat"]["id"]
        text = msg.get("text", "")

        if text == "/start":
            user_data[chat_id] = {}
            services_text = "✨ <b>Добро пожаловать в салон красоты!</b>\nВыберите услугу:\n\n"
            keyboard_inline = []
            for key, val in SERVICES.items():
                services_text += f"{key}. {val['name']} — <b>{val['price']}</b>\n"
                keyboard_inline.append([{"text": f"{val['name']} ({val['price']})", "callback_data": f"service_{key}"}])
            
            send_message(chat_id, services_text, {"inline_keyboard": keyboard_inline})

        elif chat_id in user_data and user_data[chat_id].get("step") == "wait_time":
            user_data[chat_id]["time"] = text
            client_name = msg["from"].get("first_name", "Клиент")
            username = msg["from"].get("username", "нет юзернейма")
            service = user_data[chat_id].get("service")
            master = user_data[chat_id].get("master")
            time_slot = user_data[chat_id].get("time")

            booking_str = f"Клиент: {client_name} (@{username}) | Услуга: {service} | Мастер: {master} | Время: {time_slot}"
            save_booking(booking_str)

            success_text = (
                f"✅ <b>Запись успешно оформлена!</b>\n\n"
                f"💇‍♀️ Услуга: {service}\n"
                f"✨ Мастер: {master}\n"
                f"🕒 Время: {time_slot}\n\n"
                f"Мы ждем вас в салоне!"
            )
            send_message(chat_id, success_text)

            if ADMIN_CHAT_ID != "0":
                admin_text = (
                    f"🔔 <b>Новая запись в салон!</b>\n\n"
                    f"👤 Клиент: {client_name} (@{username})\n"
                    f"💇‍♀️ Услуга: {service}\n"
                    f"✨ Мастер: {master}\n"
                    f"🕒 Время: {time_slot}"
                )
                send_message(ADMIN_CHAT_ID, admin_text)

            del user_data[chat_id]

    elif "callback_query" in update:
        query = update["callback_query"]
        chat_id = query["message"]["chat"]["id"]
        data = query["data"]

        if chat_id not in user_data:
            user_data[chat_id] = {}

        if data.startswith("service_"):
            s_key = data.split("_")[1]
            user_data[chat_id]["service"] = SERVICES[s_key]["name"]
            user_data[chat_id]["price"] = SERVICES[s_key]["price"]

            masters_text = f"Вы выбрали: <b>{user_data[chat_id]['service']}</b>\nТеперь выберите мастера:"
            keyboard_inline = []
            for key, val in MASTERS.items():
                keyboard_inline.append([{"text": val, "callback_data": f"master_{key}"}])
            
            send_message(chat_id, masters_text, {"inline_keyboard": keyboard_inline})

        elif data.startswith("master_"):
            m_key = data.split("_")[1]
            user_data[chat_id]["master"] = MASTERS[m_key]

            send_message(chat_id, f"Мастер: <b>{user_data[chat_id]['master']}</b>\nВведите удобную дату и время визита (например: <i>Завтра в 14:00</i>):")
            user_data[chat_id]["step"] = "wait_time"


# --- ЦИКЛ БОТА ---
def run_bot():
    offset = 0
    print("Telegram бот запущен в фоновом режиме.")
    while True:
        try:
            url = f"{BASE_URL}/getUpdates?offset={offset}&timeout=30"
            response = requests.get(url).json()

            if "result" in response:
                for result in response["result"]:
                    offset = result["update_id"] + 1
                    handle_update(result)
        except Exception as e:
            print(f"Ошибка в цикле бота: {e}")


# --- ГЛАВНЫЙ ЗАПУСК ---
if __name__ == "__main__":
    bot_thread = threading.Thread(target=run_bot)
    bot_thread.daemon = True
    bot_thread.start()

    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)