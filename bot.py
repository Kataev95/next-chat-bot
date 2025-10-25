# bot.py - DEBUG VERSION с подробными логами
import os
from flask import Flask, request, jsonify
from telegram import Bot, Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import Dispatcher, CommandHandler, MessageHandler, Filters
import json
from datetime import datetime
import traceback

# Конфигурация
BOT_TOKEN = os.environ.get('BOT_TOKEN', 'YOUR_BOT_TOKEN_HERE')
WEBAPP_URL = os.environ.get('WEBAPP_URL', 'https://username.github.io/next-tg-chat')

# Инициализация Flask и Telegram Bot
app = Flask(__name__)
bot = Bot(token=BOT_TOKEN)

# Хранилище активных пользователей
active_users = {}  # {user_id: {'nickname': str, 'chat_id': int}}

def log(message):
    '''Логирование с временной меткой'''
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f'[{timestamp}] {message}')

@app.route('/')
def index():
    return '''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>The Next Chat Bot - DEBUG</title>
    <style>
        body {
            font-family: 'Courier New', monospace;
            background: #0a0a0a;
            color: #0f0;
            padding: 20px;
            line-height: 1.6;
        }
        .container {
            max-width: 800px;
            margin: 0 auto;
            background: rgba(0, 255, 0, 0.05);
            padding: 20px;
            border: 2px solid #0f0;
            border-radius: 10px;
        }
        h1 { color: #0ff; text-align: center; }
        .status { color: #0f0; font-weight: bold; }
        .error { color: #f00; }
        .info { color: #ff0; }
        table { width: 100%; margin: 20px 0; border-collapse: collapse; }
        td { padding: 10px; border-bottom: 1px solid #333; }
        td:first-child { color: #0ff; font-weight: bold; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🚀 The Next Chat Bot</h1>
        <p class="status">✅ Status: Running (DEBUG MODE)</p>

        <table>
            <tr>
                <td>👥 Active Users:</td>
                <td>''' + str(len(active_users)) + '''</td>
            </tr>
            <tr>
                <td>🌐 Web App URL:</td>
                <td>''' + WEBAPP_URL + '''</td>
            </tr>
            <tr>
                <td>🔑 Bot Token:</td>
                <td>''' + BOT_TOKEN[:10] + '''...</td>
            </tr>
        </table>

        <h3>📊 Endpoints:</h3>
        <ul>
            <li><a href="/webhook-info" style="color: #0ff;">/webhook-info</a> - Check webhook status</li>
            <li><a href="/users" style="color: #0ff;">/users</a> - List active users</li>
            <li>/setwebhook?url=YOUR_URL - Set webhook</li>
        </ul>

        <h3>👥 Online Users:</h3>
        <ul>
        ''' + '\n'.join([f'<li>@{u["nickname"]} (ID: {uid})</li>' for uid, u in active_users.items()]) + '''
        </ul>
    </div>
</body>
</html>'''

@app.route('/webhook', methods=['POST'])
def webhook():
    '''Обработка входящих обновлений от Telegram'''
    try:
        log('📨 Received webhook request')
        data = request.get_json(force=True)
        log(f'📦 Raw data: {json.dumps(data)[:200]}...')

        update = Update.de_json(data, bot)
        log(f'✅ Update parsed successfully')

        if update.message:
            log(f'💬 Message from user {update.message.from_user.id}')

            if update.message.web_app_data:
                log('🌐 Web App data detected')
                handle_webapp_data(update)
            else:
                log('📝 Regular message')
                handle_message(update.message)
        else:
            log('⚠️ Update without message')

        return 'ok'
    except Exception as e:
        log(f'❌ ERROR in webhook: {e}')
        log(f'📜 Traceback: {traceback.format_exc()}')
        return 'error', 500

def handle_message(message):
    '''Обработка текстовых сообщений и команд'''
    chat_id = message.chat_id
    user_id = message.from_user.id
    log(f'📨 Handling message from user {user_id}, chat {chat_id}')

    if message.text == '/start':
        log('🚀 /start command')
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton(
                text='🚀 Открыть чат',
                web_app=WebAppInfo(url=WEBAPP_URL)
            )]
        ])

        welcome_text = f'''👋 Добро пожаловать в чат The Next! (DEBUG MODE)

🎯 Анонимный текстовый чат

✨ Возможности:
• Выбор своего никнейма
• Текстовые сообщения в реал-тайм
• Красивый неоновый дизайн

👥 Сейчас онлайн: {len(active_users)} пользователей

Нажмите кнопку ниже!'''

        bot.send_message(
            chat_id=chat_id,
            text=welcome_text,
            reply_markup=keyboard
        )
        log(f'✅ Welcome message sent to {user_id}')

    elif message.text == '/stats':
        log('📊 /stats command')
        nicknames = [u['nickname'] for u in active_users.values()]
        stats_text = f'''📊 Статистика:

👥 Активных: {len(active_users)}

Онлайн:
{chr(10).join(['• @' + n for n in nicknames[:15]])}'''

        bot.send_message(chat_id=chat_id, text=stats_text)
        log(f'✅ Stats sent to {user_id}')

    elif message.text == '/debug':
        log('🐛 /debug command')
        debug_text = f'''🐛 DEBUG INFO:

Active users: {len(active_users)}
Users: {list(active_users.keys())}

Bot Token: {BOT_TOKEN[:10]}...
Web App: {WEBAPP_URL}'''

        bot.send_message(chat_id=chat_id, text=debug_text)

def handle_webapp_data(update):
    '''Обработка данных от Telegram Web App'''
    try:
        user_id = update.message.from_user.id
        chat_id = update.message.chat_id
        raw_data = update.message.web_app_data.data

        log(f'🌐 Web App data from {user_id}')
        log(f'📦 Raw data: {raw_data}')

        data = json.loads(raw_data)
        log(f'✅ Data parsed: {data}')

        msg_type = data.get('type')
        nickname = data.get('nickname', f'user_{user_id}')

        log(f'📝 Type: {msg_type}, Nickname: {nickname}')

        # Регистрируем пользователя
        active_users[user_id] = {
            'nickname': nickname,
            'chat_id': chat_id
        }
        log(f'✅ User {user_id} registered as @{nickname}')
        log(f'👥 Total active users: {len(active_users)}')

        if msg_type == 'join':
            log(f'✨ User @{nickname} joining chat')
            broadcast_join(nickname, user_id)

        elif msg_type == 'message':
            text = data.get('text', '')
            log(f'💬 Message from @{nickname}: {text}')
            broadcast_message(data, user_id)
        else:
            log(f'⚠️ Unknown message type: {msg_type}')

    except Exception as e:
        log(f'❌ ERROR in handle_webapp_data: {e}')
        log(f'📜 Traceback: {traceback.format_exc()}')

def broadcast_join(nickname, user_id):
    '''Уведомление о входе'''
    text = f"✨ @{nickname} присоединился к чату!"
    log(f'📢 Broadcasting join: {text}')

    sent_count = 0
    for uid, user_data in active_users.items():
        if uid != user_id:
            try:
                bot.send_message(
                    chat_id=user_data['chat_id'],
                    text=text
                )
                sent_count += 1
                log(f'  ✅ Sent to user {uid}')
            except Exception as e:
                log(f'  ❌ Failed to send to {uid}: {e}')

    log(f'📊 Join notification sent to {sent_count} users')

def broadcast_message(data, sender_id):
    '''Рассылка сообщения ВСЕМ'''
    sender_nickname = data.get('nickname', active_users.get(sender_id, {}).get('nickname', f'user_{sender_id}'))
    message_text = data.get('text', '')

    log(f'📢 BROADCASTING MESSAGE')
    log(f'  From: @{sender_nickname} (ID: {sender_id})')
    log(f'  Text: {message_text}')
    log(f'  Recipients: {len(active_users) - 1} users')

    if not message_text.strip():
        log('⚠️ Empty message, skipping broadcast')
        return

    # Форматируем сообщение
    text = f"💬 @{sender_nickname}\n{message_text}"
    log(f'  Formatted: {text}')

    # Рассылаем всем кроме отправителя
    sent_count = 0
    failed_users = []

    for user_id, user_data in list(active_users.items()):
        if user_id == sender_id:
            log(f'  ⏭️ Skipping sender {user_id}')
            continue

        try:
            log(f'  📤 Sending to user {user_id} (@{user_data["nickname"]}), chat {user_data["chat_id"]}')
            bot.send_message(
                chat_id=user_data['chat_id'],
                text=text
            )
            sent_count += 1
            log(f'    ✅ SUCCESS')
        except Exception as e:
            log(f'    ❌ FAILED: {e}')
            failed_users.append(user_id)

    # Удаляем неактивных
    for user_id in failed_users:
        if user_id in active_users:
            log(f'🗑️ Removing inactive user {user_id}')
            del active_users[user_id]

    log(f'📊 BROADCAST COMPLETE: sent to {sent_count}/{len(active_users)-1} users')

@app.route('/setwebhook', methods=['GET'])
def set_webhook():
    '''Настройка webhook'''
    webhook_url = request.args.get('url')
    if not webhook_url:
        return 'Error: Use /setwebhook?url=YOUR_RENDER_URL', 400

    try:
        log(f'🔧 Setting webhook to {webhook_url}/webhook')
        result = bot.set_webhook(url=f'{webhook_url}/webhook')
        if result:
            log('✅ Webhook set successfully')
            return f'✅ Webhook set to {webhook_url}/webhook'
        else:
            log('❌ Failed to set webhook')
            return '❌ Failed to set webhook', 500
    except Exception as e:
        log(f'❌ Error setting webhook: {e}')
        return f'❌ Error: {e}', 500

@app.route('/webhook-info', methods=['GET'])
def webhook_info():
    '''Проверка webhook'''
    try:
        info = bot.get_webhook_info()
        return jsonify({
            'url': info.url,
            'pending_update_count': info.pending_update_count,
            'last_error_date': str(info.last_error_date) if info.last_error_date else None,
            'last_error_message': info.last_error_message,
            'active_users': len(active_users),
            'user_list': [{'id': uid, 'nickname': u['nickname']} for uid, u in active_users.items()]
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/users', methods=['GET'])
def get_users():
    '''Список пользователей'''
    try:
        users_list = [
            {
                'nickname': user_data['nickname'],
                'user_id': user_id,
                'chat_id': user_data['chat_id']
            }
            for user_id, user_data in active_users.items()
        ]
        return jsonify({
            'count': len(users_list),
            'users': users_list
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    log('╔═══════════════════════════════════════════════╗')
    log('║   The Next Chat Bot - DEBUG MODE             ║')
    log('╚═══════════════════════════════════════════════╝')
    log(f'Bot Token: {BOT_TOKEN[:10]}...')
    log(f'Web App URL: {WEBAPP_URL}')
    log('Starting server...')
    app.run(host='0.0.0.0', port=5000, debug=True)
