import os
import telegram
import logging
from requests import get
from requests.exceptions import ReadTimeout, ConnectionError
from textwrap import dedent
from time import sleep
from dotenv import load_dotenv


load_dotenv()


class TelegramLogsHandler(logging.Handler):
    def __init__(self):
        super().__init__()
        self.chat_id = os.environ['TG_CHATID']
        self.tg_bot = telegram.Bot(os.environ['TG_BOT_TOKEN'])

    def emit(self, record):
        log_entry = self.format(record)
        self.tg_bot.send_message(chat_id=self.chat_id, text=log_entry)


def main():
    logger = logging.getLogger('Logger')
    logger.setLevel(logging.INFO)
    logger.addHandler(TelegramLogsHandler())

    bot = telegram.Bot(os.environ['TG_BOT_TOKEN'])
    chat_id = os.environ['TG_CHATID']
    bot.send_message(chat_id=chat_id, text='Notification bot state: ON')

    api_token = os.environ['DEVMAN_TOKEN']
    timestamp = None
    headers = {'Authorization': f'Token {api_token}'}
    connect_err_count = 0

    while True:
        try:
            params = {'timestamp': timestamp}

            response = get(
                'https://dvmn.org/api/long_polling/',
                params=params,
                headers=headers,
                timeout=int(os.environ['TG_BOT_REQUEST_TIMEOUT']),
            )
            connect_err_count = 0
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
                    result = 'Преподавателю все понравилось, ' \
                             'можно приступать к следующему уроку.'
                bot.send_message(
                    chat_id=chat_id,
                    text=dedent(
                        f'''
                        Преподаватель проверил работу
                        "{attempt['lesson_title']}".
                        {result}
                        {attempt['lesson_url']}
                        '''
                    )
                )
        except ConnectionError:
            connect_err_count += 1
            if connect_err_count > 10:
                logger.exception(f'ConnectionError count: {connect_err_count}')
            sleep(100 * connect_err_count)
        except ReadTimeout:
            continue
        except Exception:
            logger.exception('Exception:')
            sleep(10)


if __name__ == '__main__':
    main()
