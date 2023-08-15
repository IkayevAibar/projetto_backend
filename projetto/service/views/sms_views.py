import requests
import random
from app.settings import sms_version_send_type

# Функция для генерации кода
def generate_code():
    # Генерируем случайный шестизначный код
    return str(random.randint(1000, 9999))

# Функция для отправки SMS
def send_sms(username, password, recipient, message):
    if(sms_version_send_type == "PROD"):
        url = 'http://kazinfoteh.org:9507/api?action=sendmessage'
        params = {
            'username': username,
            'password': password,
            'recipient': recipient,
            'messagetype': 'SMS:TEXT',
            'originator': 'INFO_KAZ',
            'messagedata': message
        }
        
        response = requests.get(url, params=params)
        # Обработка ответа
        if response.status_code == 200:
            # Отправка успешна
            return True
        else:
            # Ошибка при отправке
            return False
    else:
        return True