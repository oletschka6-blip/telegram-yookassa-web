import json
import hmac
import hashlib
import os
import requests

def handler(event, context):
    # Получаем тело запроса и заголовок с подписью
    body = event.get('body', '')
    signature = event.get('headers', {}).get('x-yookassa-signature')

    # Проверяем наличие подписи
    if not signature:
        return {
            'statusCode': 400,
            'body': json.dumps({'error': 'No signature'})
        }

    # Получаем секретный ключ из переменных окружения
    secret = os.environ.get('YOOKASSA_SECRET')
    if not secret:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Secret key not configured'})
        }

    # Рассчитываем подпись
    calculated_signature = hmac.new(
        secret.encode(),
        body.encode() if isinstance(body, str) else body,
        hashlib.sha256
    ).hexdigest()

    # Сравниваем подписи
    if signature != calculated_signature:
        return {
            'statusCode': 401,
            'body': json.dumps({'error': 'Invalid signature'})
        }

    # Парсим JSON из тела запроса
    try:
        data = json.loads(body)
    except json.JSONDecodeError:
        return {
            'statusCode': 400,
            'body': json.dumps({'error': 'Invalid JSON'})
        }

    # Обрабатываем событие (пример для успешного платежа)
    if data.get('event') == 'payment.succeeded':
        amount = data['object']['amount']['value']
        status = data['object']['status']

        # Отправляем уведомление в Telegram
        bot_token = os.environ.get('BOT_TOKEN')
        chat_id = os.environ.get('CHAT_ID')
        if not bot_token or not chat_id:
            return {
                'statusCode': 500,
                'body': json.dumps({'error': 'Telegram credentials not configured'})
            }

        message = f"💳 Новый платёж: {amount} руб. Статус: {status}"
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        requests.post(url, data={'chat_id': chat_id, 'text': message})

    return {
        'statusCode': 200,
        'body': json.dumps({'status': 'ok'})
    }
