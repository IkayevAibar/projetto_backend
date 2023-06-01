# Базовый образ, в данном случае - Python 3.8
FROM python:3.11

# Рабочая директория, где будет располагаться код приложения
WORKDIR /projetto

# Установка зависимостей
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
# RUN python manage.py makemigrations
# RUN python manage.py migrate

# Копирование кода приложения
COPY ./projetto  /projetto

# Запуск приложения
CMD ["python", "manage.py", "runserver", "0.0.0.0:8080"]
# CMD ["gunicorn", "--bind", "0.0.0.0:8080", "app.wsgi:application"]
