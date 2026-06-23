FROM postgres:15

# Копируем init.sql для инициализации базы данных
COPY init.sql /docker-entrypoint-initdb.d/

# Установка дополнительных пакетов (опционально)
RUN apt-get update && apt-get install -y \
    postgresql-contrib \
    && rm -rf /var/lib/apt/lists/*