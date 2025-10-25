# bot.py - Telegram Bot для чата The Next
import os
from flask import Flask, request, jsonify
from telegram import Bot, Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import Dispatcher, CommandHandler, MessageHandler, Filters
import json
from datetime import datetime

# Конфигурация
BOT_TOKEN = os.environ.get('BOT_TOKEN', 'YOUR_BOT_TOKEN_HERE')
WEBAPP_URL = os.environ.get('WEBAPP_URL', 'https://username.github.io/next-tg-chat')

# Инициализация Flask и Telegram Bot
app = Flask(__name__)
bot = Bot(token=BOT_TOKEN)

# Хранилище активных пользователей и сообщений (в реальном проекте использовать БД)
active_users = {}  # {user_id: {'username': str, 'first_name': str, 'chat_id': int}}
messages = []  # [{id, user_id, username, text, timestamp, type}]

@app.route('/')
def index():
    return 'The Next Chat Bot is running! 🚀'

@app.route('/webhook', methods=['POST'])
def webhook():
    '''Обработка входящих обновлений от Telegram'''
    try:
        update = Update.de_json(request.get_json(force=True), bot)

        # Обработка веб-данных от Telegram Web App
        if update.message and update.message.web_app_data:
            handle_webapp_data(update)
        # Обработка обычных команд
        elif update.message:
            handle_message(update.message)

        return 'ok'
    except Exception as e:
        print(f'Error: {e}')
        return 'error', 500

def handle_message(message):
    '''Обработка текстовых сообщений и команд'''
    chat_id = message.chat_id
    user_id = message.from_user.id

    if message.text == '/start':
        # Приветственное сообщение с кнопкой Web App
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton(
                text='🚀 Открыть чат',
                web_app=WebAppInfo(url=WEBAPP_URL)
            )]
        ])

        welcome_text = f'''👋 Добро пожаловать в чат The Next!

Нажмите кнопку ниже, чтобы открыть анонимный чат.
Все участники могут общаться в реальном времени.

✨ Возможности:
• Текстовые сообщения
• Голосовые сообщения
• Изображения и видео
• Ответы и упоминания
• Неоновый дизайн

Присоединяйтесь к {len(active_users)} активным пользователям!'''

        bot.send_message(
            chat_id=chat_id,
            text=welcome_text,
            reply_markup=keyboard
        )

        # Регистрируем пользователя
        active_users[user_id] = {
            'username': message.from_user.username or f'user_{user_id}',
            'first_name': message.from_user.first_name,
            'chat_id': chat_id
        }

        print(f'New user registered: {message.from_user.first_name} (ID: {user_id})')

    elif message.text == '/stats':
        # Статистика чата
        stats_text = f'''📊 Статистика чата The Next:

👥 Активных пользователей: {len(active_users)}
💬 Всего сообщений: {len(messages)}
🎉 Чат работает!'''

        bot.send_message(chat_id=chat_id, text=stats_text)

def handle_webapp_data(update):
    '''Обработка данных от Telegram Web App'''
    try:
        user_id = update.message.from_user.id
        chat_id = update.message.chat_id
        data = json.loads(update.message.web_app_data.data)

        # Регистрируем пользователя если еще не зарегистрирован
        if user_id not in active_users:
            active_users[user_id] = {
                'username': update.message.from_user.username or f'user_{user_id}',
                'first_name': update.message.from_user.first_name,
                'chat_id': chat_id
            }

        msg_type = data.get('type')

        if msg_type == 'message':
            # Текстовое сообщение
            broadcast_message(data, user_id)

        elif msg_type == 'voice':
            # Голосовое сообщение
            broadcast_voice(data, user_id)

        elif msg_type == 'image':
            # Изображение
            broadcast_image(data, user_id)

        elif msg_type == 'video':
            # Видео
            broadcast_video(data, user_id)

    except Exception as e:
        print(f'Error handling webapp data: {e}')

def broadcast_message(data, sender_id):
    '''Отправка текстового сообщения всем активным пользователям'''
    message = {
        'id': len(messages) + 1,
        'user_id': sender_id,
        'username': active_users[sender_id]['username'],
        'first_name': active_users[sender_id]['first_name'],
        'text': data.get('text', ''),
        'timestamp': datetime.now().isoformat(),
        'type': 'text',
        'reply_to_id': data.get('reply_to_id'),
        'mentions': data.get('mentions', [])
    }

    messages.append(message)
    print(f'New message from {message["first_name"]}: {message["text"]}')

    # Форматируем сообщение для отправки
    text = f"💬 {message['first_name']}: {message['text']}"

    # Отправляем всем активным пользователям
    sent_count = 0
    for user_id, user_data in active_users.items():
        if user_id != sender_id:  # Не отправляем отправителю
            try:
                bot.send_message(
                    chat_id=user_data['chat_id'],
                    text=text
                )
                sent_count += 1
            except Exception as e:
                print(f'Error sending to user {user_id}: {e}')

    print(f'Message broadcasted to {sent_count} users')

def broadcast_voice(data, sender_id):
    '''Отправка голосового сообщения'''
    text = f"🎤 {active_users[sender_id]['first_name']} отправил(а) голосовое сообщение"

    for user_id, user_data in active_users.items():
        if user_id != sender_id:
            try:
                bot.send_message(chat_id=user_data['chat_id'], text=text)
            except:
                pass

def broadcast_image(data, sender_id):
    '''Отправка изображения'''
    text = f"🖼 {active_users[sender_id]['first_name']} отправил(а) изображение"

    for user_id, user_data in active_users.items():
        if user_id != sender_id:
            try:
                bot.send_message(chat_id=user_data['chat_id'], text=text)
            except:
                pass

def broadcast_video(data, sender_id):
    '''Отправка видео'''
    text = f"🎥 {active_users[sender_id]['first_name']} отправил(а) видео"

    for user_id, user_data in active_users.items():
        if user_id != sender_id:
            try:
                bot.send_message(chat_id=user_data['chat_id'], text=text)
            except:
                pass

@app.route('/setwebhook', methods=['GET'])
def set_webhook():
    '''Настройка webhook (вызывается один раз при развертывании)'''
    webhook_url = request.args.get('url')
    if not webhook_url:
        return 'Error: No webhook URL provided. Use: /setwebhook?url=YOUR_RENDER_URL', 400

    try:
        result = bot.set_webhook(url=f'{webhook_url}/webhook')
        if result:
            return f'✅ Webhook successfully set to {webhook_url}/webhook'
        else:
            return '❌ Failed to set webhook', 500
    except Exception as e:
        return f'❌ Error setting webhook: {e}', 500

@app.route('/webhook-info', methods=['GET'])
def webhook_info():
    '''Проверка текущего webhook'''
    try:
        info = bot.get_webhook_info()
        return jsonify({
            'url': info.url,
            'pending_update_count': info.pending_update_count,
            'last_error_date': info.last_error_date,
            'last_error_message': info.last_error_message
        })
    except Exception as e:
        return f'Error: {e}', 500

if __name__ == '__main__':
    # Для локальной разработки
    print('Starting The Next Chat Bot...')
    print(f'Bot Token: {BOT_TOKEN[:10]}...')
    print(f'Web App URL: {WEBAPP_URL}')
    app.run(host='0.0.0.0', port=5000, debug=True)
