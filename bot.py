# bot.py - Telegram Bot для чата The Next (только текст)
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

# Хранилище активных пользователей
active_users = {}  # {user_id: {'nickname': str, 'chat_id': int}}

@app.route('/')
def index():
    return '''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>The Next Chat Bot</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            display: flex;
            align-items: center;
            justify-content: center;
            height: 100vh;
            margin: 0;
        }
        .container {
            text-align: center;
            padding: 40px;
            background: rgba(255,255,255,0.1);
            border-radius: 20px;
            backdrop-filter: blur(10px);
        }
        h1 { font-size: 48px; margin-bottom: 10px; }
        p { font-size: 18px; margin: 10px 0; }
        .status { color: #0f0; font-weight: bold; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🚀 The Next Chat Bot</h1>
        <p class="status">✅ Running</p>
        <p>👥 Active users: ''' + str(len(active_users)) + '''</p>
        <p>💬 Text-only anonymous chat</p>
    </div>
</body>
</html>'''

@app.route('/webhook', methods=['POST'])
def webhook():
    '''Обработка входящих обновлений от Telegram'''
    try:
        update = Update.de_json(request.get_json(force=True), bot)

        if update.message and update.message.web_app_data:
            handle_webapp_data(update)
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
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton(
                text='🚀 Открыть чат',
                web_app=WebAppInfo(url=WEBAPP_URL)
            )]
        ])

        welcome_text = f'''👋 Добро пожаловать в чат The Next!

🎯 Анонимный текстовый чат для вашей группы

✨ Возможности:
• Выбор своего никнейма
• Текстовые сообщения в реал-тайм
• Упоминания @nickname
• Красивый неоновый дизайн
• Полная анонимность

👥 Сейчас онлайн: {len(active_users)} пользователей

Нажмите кнопку ниже, чтобы начать общение!'''

        bot.send_message(
            chat_id=chat_id,
            text=welcome_text,
            reply_markup=keyboard
        )

        print(f'User {user_id} started bot')

    elif message.text == '/stats':
        nicknames = [u['nickname'] for u in active_users.values()]
        stats_text = f'''📊 Статистика чата The Next:

👥 Активных пользователей: {len(active_users)}

💬 Онлайн сейчас:
{chr(10).join(['• @' + n for n in nicknames[:15]])}
{f'...и ещё {len(nicknames)-15}' if len(nicknames) > 15 else ''}

🎉 Чат работает!'''

        bot.send_message(chat_id=chat_id, text=stats_text)

def handle_webapp_data(update):
    '''Обработка данных от Telegram Web App'''
    try:
        user_id = update.message.from_user.id
        chat_id = update.message.chat_id
        data = json.loads(update.message.web_app_data.data)

        msg_type = data.get('type')
        nickname = data.get('nickname', f'user_{user_id}')

        # Регистрируем/обновляем пользователя
        active_users[user_id] = {
            'nickname': nickname,
            'chat_id': chat_id
        }

        if msg_type == 'join':
            broadcast_join(nickname, user_id)
            print(f'@{nickname} joined the chat (ID: {user_id})')

        elif msg_type == 'message':
            broadcast_message(data, user_id)

    except Exception as e:
        print(f'Error handling webapp data: {e}')

def broadcast_join(nickname, user_id):
    '''Уведомление о входе нового пользователя'''
    text = f"✨ @{nickname} присоединился к чату!"

    sent_count = 0
    for uid, user_data in active_users.items():
        if uid != user_id:
            try:
                bot.send_message(
                    chat_id=user_data['chat_id'],
                    text=text
                )
                sent_count += 1
            except Exception as e:
                print(f'Error sending join to user {uid}: {e}')

    print(f'Join notification sent to {sent_count} users')

def broadcast_message(data, sender_id):
    '''Рассылка текстового сообщения ВСЕМ активным пользователям'''
    sender_nickname = data.get('nickname', active_users.get(sender_id, {}).get('nickname', f'user_{sender_id}'))
    message_text = data.get('text', '')

    if not message_text.strip():
        return

    print(f'Broadcasting from @{sender_nickname}: {message_text[:50]}...')

    # Форматируем сообщение
    text = f"💬 @{sender_nickname}\n{message_text}"

    # Рассылаем всем кроме отправителя
    sent_count = 0
    failed_users = []

    for user_id, user_data in list(active_users.items()):
        if user_id == sender_id:
            continue

        try:
            bot.send_message(
                chat_id=user_data['chat_id'],
                text=text
            )
            sent_count += 1
        except Exception as e:
            print(f'Error sending to user {user_id}: {e}')
            failed_users.append(user_id)

    # Удаляем неактивных пользователей
    for user_id in failed_users:
        if user_id in active_users:
            del active_users[user_id]
            print(f'Removed inactive user {user_id}')

    print(f'Message broadcasted to {sent_count} users')

@app.route('/setwebhook', methods=['GET'])
def set_webhook():
    '''Настройка webhook'''
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
    '''Проверка webhook'''
    try:
        info = bot.get_webhook_info()
        return jsonify({
            'url': info.url,
            'pending_update_count': info.pending_update_count,
            'last_error_date': info.last_error_date,
            'last_error_message': info.last_error_message,
            'active_users': len(active_users)
        })
    except Exception as e:
        return f'Error: {e}', 500

@app.route('/users', methods=['GET'])
def get_users():
    '''Список активных пользователей'''
    try:
        users_list = [
            {
                'nickname': user_data['nickname'],
                'user_id': user_id
            }
            for user_id, user_data in active_users.items()
        ]
        return jsonify({
            'count': len(users_list),
            'users': users_list
        })
    except Exception as e:
        return f'Error: {e}', 500

if __name__ == '__main__':
    print('╔═══════════════════════════════════════════════╗')
    print('║     The Next Chat Bot - Starting...          ║')
    print('╚═══════════════════════════════════════════════╝')
    print(f'Bot Token: {BOT_TOKEN[:10]}...')
    print(f'Web App URL: {WEBAPP_URL}')
    print('Features: Text messages only (no media/voice)')
    app.run(host='0.0.0.0', port=5000, debug=True)
