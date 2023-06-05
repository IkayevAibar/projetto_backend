import hashlib
import requests
import random
import string
import urllib.parse

url = "https://api.paybox.money/init_payment.php"

script_name = urllib.parse.urlparse(url).path.split('/')[-1]
print(script_name)

pg_amount = '250'
pg_currency = 'KZT'
pg_description = 'Description of payment'
pg_merchant_id = '548856'
pg_card_name = 'TESTD TESTOVD'
pg_card_pan = '4444444444446666'
pg_card_cvc = '123'
pg_card_month = '12'
pg_card_year = '24'
pg_auto_clearing = '1'
pg_testing_mode = '1'
pg_result_url = 'localhost'
pg_3ds_challenge = '1'
pg_param1 = ''
pg_param2 = ''
pg_param3 = ''

# Генерация случайной строки для pg_salt
def generate_salt(length):
    letters_and_digits = string.ascii_letters + string.digits
    return ''.join(random.choice(letters_and_digits) for i in range(length))

pg_order_id = '1244'  # Уникальный идентификатор заказа для каждого запроса
pg_salt = generate_salt(16)  # Уникальная случайная строка для каждого запроса

print(pg_salt)

secret_key = "lU86k8y7lBrdj0E6"

data = {
    'pg_amount': pg_amount,
    'pg_currency': pg_currency,
    'pg_description': pg_description,
    'pg_merchant_id': pg_merchant_id,
    'pg_order_id': pg_order_id,
    'pg_card_name': pg_card_name,
    'pg_card_pan': pg_card_pan,
    'pg_card_cvc': pg_card_cvc,
    'pg_card_month': pg_card_month,
    'pg_card_year': pg_card_year,
    'pg_auto_clearing': pg_auto_clearing,
    'pg_testing_mode': pg_testing_mode,
    'pg_result_url': pg_result_url,
    'pg_3ds_challenge': pg_3ds_challenge,
    'pg_param1': pg_param1,
    'pg_param2': pg_param2,
    'pg_param3': pg_param3,
    'pg_salt': pg_salt
}

# Сортировка параметров по ключу в алфавитном порядке
sorted_data = sorted(data.items(), key=lambda x: x[0])

# Формирование строки для подписи
data_string = ';'.join([f"{value}" for key, value in sorted_data])

# Формирование строки для подписи с добавлением секретного ключа
data_with_secret_key = f"{script_name};{data_string};{secret_key}"
data_with_secret_key_encoded = data_with_secret_key.encode('latin-1')
print(data_with_secret_key)

md5_hash = hashlib.md5(data_with_secret_key_encoded)
pg_sig = md5_hash.hexdigest()

print(pg_sig)
print(len(pg_sig))

payload = {**data, 'pg_sig': pg_sig}

response = requests.post(url, data=payload)

print(response.status_code)
print(response.text)