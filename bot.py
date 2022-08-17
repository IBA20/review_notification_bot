import os
import telegram
import logging
from requests import get


class TelegramLogsHandler(logging.Handler):
    def __init__(self, tg_bot, chat_id):
        super().__init__()
        self.chat_id = chat_id
        self.tg_bot = tg_bot

    def emit(self, record):
        log_entry = self.format(record)
        self.tg_bot.send_message(chat_id=self.chat_id, text=log_entry)


bot = telegram.Bot(os.environ['TG_BOT_TOKEN'])
chat_id = os.environ['TG_CHATID']

logger = logging.getLogger('database')
logger.setLevel(logging.INFO)
logger.addHandler(TelegramLogsHandler(bot, chat_id))
logger.info('Notification bot state: ON')

api_token = os.environ['DEVMAN_TOKEN']
timestamp = None
headers = {'Authorization': f'Token {api_token}'}
while True:
    try:
        params = {'timestamp': timestamp}
        response = get(
            'https://dvmn.org/api/long_polling/',
            params=params,
            headers=headers,
            timeout=int(os.environ['TG_BOT_REQUEST_TIMEOUT']),
        )
        response.raise_for_status()
        review_data = response.json()
        if review_data['status'] != 'found':
            timestamp = review_data['timestamp_to_request']
            continue
        timestamp = review_data['last_attempt_timestamp']
        for attempt in review_data["new_attempts"]:
            if attempt['is_negative']:
                result = 'К сожалению, в работе нашлись ошибки.'
            else:
                result = 'Преподавателю все понравилось, можно приступать' \
                         ' к следующему уроку.'
            logger.info(
                f"Преподаватель проверил работу"
                f" \"{attempt['lesson_title']}\""
                f"\n{result}\n{attempt['lesson_url']}"
            )
    except Exception:
        logger.exception('Error:')
