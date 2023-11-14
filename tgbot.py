import requests
import json

class TgBot:
    def __init__(self, token):
        self.token = token

    def send_message(self, chat_id, text, **kwargs):
        data={
            'chat_id': chat_id,
            'text': text,
            **kwargs
        }
        req = requests.post(
            url='https://api.telegram.org/bot{0}/{1}'.format(self.token, "sendMessage"),
            data=data).json()
        return req

    def send_message_inline(self, chat_id, text,reply_markup, **kwargs):
        data={
            'chat_id': chat_id,
            'text': text,
            'reply_markup': json.dumps(reply_markup),
            **kwargs
        }
        req = requests.post(
            url='https://api.telegram.org/bot{0}/{1}'.format(self.token, "sendMessage"),
            data=data).json()
        return req
