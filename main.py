import time
from datetime import datetime
import requests

# 1. Вставьте ваш токен от BotFather в кавычки
TOKEN = "9200361744:AAGZd7cuSCgdm3Cw2tpU3QKqQbGNJennAvU"
# 2. Вставьте ваш числовой Telegram ID, чтобы получать уведомления администратора
ADMIN_CHAT_ID = 7050276939  # Замените на ваш настоящий ID (число без кавычек)

URL = f"https://api.telegram.org/bot{TOKEN}"

user_sessions = {}

def send_message(chat_id, text, reply_markup=None):
    url = f"{URL}/sendMessage"
    payload = {
        "chat_id": chat_id, 
        "text": text, 
        "parse_mode": "HTML"
    }
    if reply_markup:
        payload["reply_markup"] = reply_markup
    
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print("Помилка відправки:", e)

def save_booking(user_id, user_name, service, master, date, time_slot):
    """Сохранение записи в файл bookings.txt и уведомление админа"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    entry = f"{user_id}|{user_name}|{service}|{master}|{date}|{time_slot}|{now}\n"
    with open("bookings.txt", "a", encoding="utf-8") as f:
        f.write(entry)
    
    # Отправка уведомления администратору
    admin_text = (
        f"🔔 <b>Новий запис у салоні!</b>\n\n"
        f"👤 Клієнт: {user_name} (ID: {user_id})\n"
        f"💅 Послуга: {service}\n"
        f"👩‍🎨 Майстер: {master}\n"
        f"📅 Дата: {date}\n"
        f"⏰ Час: {time_slot}"
    )
    send_message(ADMIN_CHAT_ID, admin_text)

def get_user_bookings(user_id):
    """Получение списка записей конкретного пользователя"""
    try:
        with open("bookings.txt", "r", encoding="utf-8") as f:
            lines = f.readlines()
        user_list = []
        for line in lines:
            parts = line.strip().split("|")
            if len(parts) >= 7 and parts[0] == str(user_id):
                user_list.append({
                    "service": parts[2], 
                    "master": parts[3], 
                    "date": parts[4], 
                    "time": parts[5], 
                    "name": parts[1]
                })
        return user_list
    except FileNotFoundError:
        return []

def cancel_user_booking(user_id, service_to_cancel):
    """Отмена записи и уведомление администратора"""
    try:
        with open("bookings.txt", "r", encoding="utf-8") as f:
            lines = f.readlines()
        
        new_lines = []
        cancelled_info = None
        cancelled = False
        
        for line in lines:
            parts = line.strip().split("|")
            if len(parts) >= 7 and parts[0] == str(user_id) and parts[2] == service_to_cancel and not cancelled:
                cancelled = True
                cancelled_info = {"name": parts[1], "service": parts[2], "master": parts[3], "date": parts[4], "time": parts[5]}
                continue
            new_lines.append(line)
            
        with open("bookings.txt", "w", encoding="utf-8") as f:
            f.writelines(new_lines)
            
        # Если отмена прошла успешно — уведомляем админа
        if cancelled and cancelled_info:
            admin_text = (
                f"❌ <b>Скасування запису!</b>\n\n"
                f"👤 Клієнт: {cancelled_info['name']} (ID: {user_id})\n"
                f"💅 Послуга: {cancelled_info['service']}\n"
                f"👩‍🎨 Майстер: {cancelled_info['master']}\n"
                f"📅 Дата: {cancelled_info['date']}\n"
                f"⏰ Час: {cancelled_info['time']}"
            )
            send_message(ADMIN_CHAT_ID, admin_text)
            
        return cancelled
    except FileNotFoundError:
        return False

def main():
    print("🚀 Бот BeautyFlow з адмін-сповіщеннями запущен! Очікування повідомлень...")
    offset = None
    
    main_keyboard = {
        "keyboard": [
            [{"text": "💅 Записатися на процедуру"}],
            [{"text": "📋 Мої записи"}, {"text": "ℹ️ Наші послуги"}],
            [{"text": "📍 Контакти салону"}]
        ],
        "resize_keyboard": True
    }

    services_keyboard = {
        "keyboard": [
            [{"text": "💅 Манікюр"}, {"text": "💇‍♀️ Стрижка"}],
            [{"text": "💄 Макіяж"}, {"text": "⬅️ Назад до меню"}]
        ],
        "resize_keyboard": True
    }

    masters_keyboard = {
        "keyboard": [
            [{"text": "👩‍🦰 Анна (ТоП-майстер)"}, {"text": "👩‍🎨 Марія (Майстер)"}],
            [{"text": "⬅️ Назад до послуг"}]
        ],
        "resize_keyboard": True
    }

    dates_keyboard = {
        "keyboard": [
            [{"text": "Сьогодні"}, {"text": "Завтра"}],
            [{"text": "Післязавтра"}],
            [{"text": "⬅️ Назад до майстрів"}]
        ],
        "resize_keyboard": True
    }

    time_keyboard = {
        "keyboard": [
            [{"text": "10:00"}, {"text": "12:00"}, {"text": "15:00"}],
            [{"text": "17:00"}, {"text": "19:00"}],
            [{"text": "⬅️ Назад до дат"}]
        ],
        "resize_keyboard": True
    }

    while True:
        try:
            response = requests.get(f"{URL}/getUpdates", params={"offset": offset, "timeout": 30}, timeout=35)
            data = response.json()
            updates = data.get("result", [])
            
            for update in updates:
                offset = update["update_id"] + 1
                if "message" in update and "text" in update["message"]:
                    chat_id = update["message"]["chat"]["id"]
                    text = update["message"]["text"]
                    user_name = update["message"]["from"].get("first_name", "Користувач")
                    
                    if chat_id not in user_sessions:
                        user_sessions[chat_id] = {"step": "menu"}
                    
                    state = user_sessions[chat_id]

                    if text in ["/start", "⬅️ Назад до меню"]:
                        state["step"] = "menu"
                        send_message(
                            chat_id, 
                            f"Вітаю, <b>{user_name}</b>! 👋\n\nЛаскаво просимо до салонного боту <b>BeautyFlow Bot</b>. Оберіть потрібну дію в меню нижче:",
                            reply_markup=main_keyboard
                        )
                    elif text == "💅 Записатися на процедуру":
                        state["step"] = "service"
                        send_message(chat_id, "<b>Крок 1/4:</b> Оберіть категорію процедури:", reply_markup=services_keyboard)
                    elif state["step"] == "service" and text in ["💅 Манікюр", "💇‍♀️ Стрижка", "💄 Макіяж"]:
                        state["service"] = text
                        state["step"] = "master"
                        send_message(chat_id, f"Ви обрали: <b>{text}</b>.\n\n<b>Крок 2/4:</b> Оберіть майстра:", reply_markup=masters_keyboard)
                    elif text == "⬅️ Назад до послуг":
                        state["step"] = "service"
                        send_message(chat_id, "Оберіть категорію процедури:", reply_markup=services_keyboard)
                    elif state["step"] == "master" and text in ["👩‍🦰 Анна (ТоП-майстер)", "👩‍🎨 Марія (Майстер)"]:
                        state["master"] = text
                        state["step"] = "date"
                        send_message(chat_id, f"Майстер: <b>{text}</b>.\n\n<b>Крок 3/4:</b> Оберіть зручну дату:", reply_markup=dates_keyboard)
                    elif text == "⬅️ Назад до майстрів":
                        state["step"] = "master"
                        send_message(chat_id, "Оберіть майстра:", reply_markup=masters_keyboard)
                    elif state["step"] == "date" and text in ["Сьогодні", "Завтра", "Післязавтра"]:
                        state["date"] = text
                        state["step"] = "time"
                        send_message(chat_id, f"Дата: <b>{text}</b>.\n\n<b>Крок 4/4:</b> Оберіть час візиту:", reply_markup=time_keyboard)
                    elif text == "⬅️ Назад до дат":
                        state["step"] = "date"
                        send_message(chat_id, "Оберіть зручну дату:", reply_markup=dates_keyboard)
                    elif state["step"] == "time" and text in ["10:00", "12:00", "15:00", "17:00", "19:00"]:
                        state["time"] = text
                        save_booking(chat_id, user_name, state["service"], state["master"], state["date"], state["time"])
                        state["step"] = "menu"
                        send_message(
                            chat_id, 
                            f"✅ <b>Вітаємо, ви успішно записані!</b>\n\n"
                            f"💅 <b>Послуга:</b> {state['service']}\n"
                            f"👤 <b>Майстер:</b> {state['master']}\n"
                            f"📅 <b>Дата:</b> {state['date']}\n"
                            f"⏰ <b>Час:</b> {state['time']}\n\n"
                            f"Адміністратор вже отримав сповіщення про ваш візит. Чекаємо на вас у салоні BeautyFlow! 🌸",
                            reply_markup=main_keyboard
                        )
                    elif text == "📋 Мої записи":
                        bookings = get_user_bookings(chat_id)
                        if not bookings:
                            send_message(chat_id, "У вас поки немає активних записів.", reply_markup=main_keyboard)
                        else:
                            msg = "📋 <b>Ваші актуальні записи:</b>\n\n"
                            cancel_kb = []
                            for idx, b in enumerate(bookings, 1):
                                msg += f"{idx}. <b>{b['service']}</b>\n   👤 {b['master']} | 📅 {b['date']} о {b['time']}\n\n"
                                cancel_kb.append([{"text": f"❌ Скасувати: {b['service']}"}])
                            cancel_kb.append([{"text": "⬅️ Назад до меню"}])
                            send_message(chat_id, msg, reply_markup={"keyboard": cancel_kb, "resize_keyboard": True})
                    elif text.startswith("❌ Скасувати: "):
                        service_to_cancel = text.replace("❌ Скасувати: ", "").strip()
                        success = cancel_user_booking(chat_id, service_to_cancel)
                        if success:
                            send_message(chat_id, f"✅ Запис на послугу <b>{service_to_cancel}</b> успішно скасовано.", reply_markup=main_keyboard)
                        else:
                            send_message(chat_id, "Не вдалося знайти такий запис.", reply_markup=main_keyboard)
                    elif text == "ℹ️ Наші послуги":
                        send_message(
                            chat_id, 
                            "📋 <b>Каталог послуг та цін BeautyFlow:</b>\n\n"
                            "💅 <b>Манікюр з покриттям</b> — від 600 грн\n"
                            "💇‍♀️ <b>Жіноча стрижка</b> — від 500 грн\n"
                            "💄 <b>Весільний макіяж</b> — від 800 грн",
                            reply_markup=main_keyboard
                        )
                    elif text == "📍 Контакти салону":
                        send_message(
                            chat_id, 
                            "📍 <b>Салон краси BeautyFlow</b>\n\n"
                            "🏙️ м. Київ, вул. Хрещатик, 1\n"
                            "📞 Телефон: +380 (99) 123-45-67",
                            reply_markup=main_keyboard
                        )
                    else:
                        send_message(chat_id, "Будь ласка, скористайтеся кнопками нижче 👇", reply_markup=main_keyboard)
        except Exception as e:
            print("Помилка:", e)
            time.sleep(3)

if __name__ == "__main__":
    main()