запуск:
docker-compose up --build

дроп:
docker-compose down -v 

инфо контейнеров:
docker ps

вход в контейнер:
docker exec -it <id> bash

подключение к бд:
psql -U user -d user_logs_db

список таблиц:
\dt

SQL проверка:
SELECT 
    u.userid, 
    u.courseid, 
    d.name AS department_name
FROM 
    user_logs u
JOIN 
    departments d ON u.Depart = d.id
LIMIT 10;

выход:
q && exit

GIT КОМАНДЫ (ЧТОБЫ ВСПОМНИТЬ):
git pull origin main --allow-unrelated-histories --no-edit (получить версию с git)
gid add . (добавить всё в коммит)
git commit -m "<text>" (создать коммит)
git branch -M main (отправка в ветку)
git push -u origin main (пуш в мейн)

