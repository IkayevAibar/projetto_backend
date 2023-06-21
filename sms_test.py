import requests
import random

# Функция для генерации кода
def generate_code():
    # Генерируем случайный шестизначный код
    return str(random.randint(100000, 999999))

# Функция для отправки SMS
def send_sms(username, password, recipient, message):
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
        print('SMS успешно отправлено')
        return True
    else:
        # Ошибка при отправке
        print('Ошибка при отправке SMS')
        return False

# Генерируем код и отправляем SMS
username = 'projetto1'
password = '0Es2doJDr'
recipient = '77066635572'

# Генерируем код
code = generate_code()

# Создаем текст сообщения
message = f'Код для подтверждения регистрации Projetto.kz: {code}'

# Отправляем SMS
if send_sms(username, password, recipient, message):
    # Отправка SMS прошла успешно, ждем подтверждения кода
    user_input = input('Введите полученный код подтверждения: ')
    if user_input == code:
        print('Код подтвержден')
    else:
        print('Неверный код подтверждения')
else:
    # Ошибка при отправке SMS
    print('Не удалось отправить SMS')
