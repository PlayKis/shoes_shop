# Shoes Shop - Интернет-магазин обуви

Django-проект для интернет-магазина обуви с системой управления товарами и заказами.

## Требования

- Python 3.10+
- Django 6.0+

## Установка

1. Клонируйте репозиторий:
```bash
git clone <repository-url>
cd shoes_shop
```

2. Создайте виртуальное окружение:
```bash
python -m venv .venv
```

3. Активируйте виртуальное окружение:
```bash
# Windows
.venv\Scripts\activate

# Linux/Mac
source .venv/bin/activate
```

4. Установите зависимости:
```bash
pip install -r requirements.txt
```

5. Примените миграции:
```bash
python manage.py migrate
```

6. Запустите сервер:
```bash
python manage.py runserver
```

7. Откройте в браузере: http://127.0.0.1:8000

## Тестовые пользователи

После миграций создайте пользователей вручную через админку или shell:

```bash
python manage.py shell
```

Создание пользователя с ролью:
```python
from django.contrib.auth.models import User
from store.models import UserProfile

user = User.objects.create_user('admin', 'admin@test.com', 'password123')
UserProfile.objects.create(user=user, role='admin')
```

## Роли пользователей

- **Гость** - просмотр товаров, добавление в корзину
- **Клиент** - оформление заказов
- **Менеджер** - просмотр товаров, поиск, фильтрация, просмотр заказов
- **Администратор** - полный доступ: CRUD товаров и заказов

## Функционал

- Каталог товаров с фильтрацией по категориям
- Поиск по товарам (для менеджера/админа)
- Сортировка по остатку (для менеджера/админа)
- Пагинация (12 товаров на странице)
- Корзина покупок
- Управление заказами (админ)
- Добавление/редактирование товаров (админ)

## Структура проекта

```
shoes_shop/
├── shoes_shop/          # Конфигурация Django
│   ├── settings.py     # Настройки проекта
│   ├── urls.py         # URL маршруты
│   └── wsgi.py         # WSGI-конфигурация
├── store/              # Приложение магазина
│   ├── models.py       # Модели данных
│   ├── views.py       # Представления
│   ├── urls.py        # URL маршруты
│   ├── admin.py       # Настройки админки
│   ├── templates/     # HTML-шаблоны
│   │   └── store/
│   └── static/         # Статические файлы
│       └── images/
├── manage.py          # Django-команды
├── requirements.txt   # Зависимости
└── db.sqlite3        # База данных
```