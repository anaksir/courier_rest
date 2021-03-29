# slasty

REST API сервис, который позволяет нанимать курьеров на работу,
принимать заказы и оптимально распределять заказы между курьерами,
попутно считая их рейтинг и заработок.

Документация (swagger), созданная с помощью drf-spectacular, 
доступна по пути /docs после запуска сервера.

Зависимости в requirements.txt.

Django REST, БД PostgreSQL.
Сервис запускается через docker-compose.
Для запуска:
1. Клонировать репозиторий в какую-нибудь папку:

git clone git@github.com:anaksir/courier_rest.git .

2. Запустить docker-compose:

docker-compose up -d --build

При отсутствии ошибок сервер Django REST будет запущен на 0.0.0.0:8080

3. При первом запуске применить миграции:

docker-compose exec web python manage.py makemigrations

docker-compose exec web python manage.py migrate

4. Для запуска тестов выполнить:

docker-compose exec web python manage.py test