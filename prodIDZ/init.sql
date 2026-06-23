-- Создание схем
CREATE SCHEMA IF NOT EXISTS public;
CREATE SCHEMA IF NOT EXISTS mart;

-- Создание расширений
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";