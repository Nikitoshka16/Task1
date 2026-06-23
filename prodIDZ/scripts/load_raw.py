"""
Модуль для загрузки данных из CSV-файлов в PostgreSQL.

Загружаемые таблицы:
- owners: владельцы недвижимости
- properties: объекты недвижимости
- price_history: ценовой архив
- transactions: сделки

Порядок загрузки важен из-за внешних ключей:
owners → properties → price_history → transactions
"""

import os
import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv('/opt/airflow/scripts/.env')


def load_csv_to_db():
    """Загружает данные из CSV-файлов в PostgreSQL"""
    
    host=os.getenv('DB_HOST', 'localhost')
    port=os.getenv('DB_PORT', '5432')
    database=os.getenv('DB_NAME', 'real_estate_db')
    user=os.getenv('DB_USER', 'admin')
    password=os.getenv('DB_PASSWORD', 'admin')
    
    engine = create_engine(f'postgresql://{user}:{password}@{host}:{port}/{database}')
    data_dir = '/opt/airflow/data'
    
    # Очистка старых данных
    with engine.begin() as conn:
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS public;"))
        
        # Удаляем сырые таблицы
        conn.execute(text("""
            DROP TABLE IF EXISTS
                public.transactions,
                public.price_history,
                public.properties,
                public.owners
            CASCADE;
        """))
    
    # Загрузка CSV
    tables = [
        ('owners', 'owners.csv'),
        ('properties', 'properties.csv'),
        ('price_history', 'price_history.csv'),
        ('transactions', 'transactions.csv')
    ]
    
    for table_name, file_name in tables:
        file_path = os.path.join(data_dir, file_name)
        if not os.path.exists(file_path):
            print(f"Файл {file_path} не найден! Пропускаем...")
            continue
            
        df = pd.read_csv(file_path)
        df.to_sql(table_name, engine, schema='public', if_exists='append', index=False)
        print(f"{table_name}: {len(df)} записей")
    
    # Создание структуры БД
    with engine.begin() as conn:
        # Первичные ключи
        conn.execute(text("ALTER TABLE public.owners ADD PRIMARY KEY (owner_id);"))
        conn.execute(text("ALTER TABLE public.properties ADD PRIMARY KEY (property_id);"))
        conn.execute(text("ALTER TABLE public.price_history ADD PRIMARY KEY (price_history_id);"))
        conn.execute(text("ALTER TABLE public.transactions ADD PRIMARY KEY (transaction_id);"))
        
        # Внешние ключи
        conn.execute(text("""
            ALTER TABLE public.transactions
            ADD CONSTRAINT fk_transactions_property
            FOREIGN KEY (property_id) REFERENCES public.properties(property_id);
        """))
        
        conn.execute(text("""
            ALTER TABLE public.transactions
            ADD CONSTRAINT fk_transactions_seller
            FOREIGN KEY (seller_id) REFERENCES public.owners(owner_id);
        """))
        
        conn.execute(text("""
            ALTER TABLE public.transactions
            ADD CONSTRAINT fk_transactions_buyer
            FOREIGN KEY (buyer_id) REFERENCES public.owners(owner_id);
        """))
        
        conn.execute(text("""
            ALTER TABLE public.price_history
            ADD CONSTRAINT fk_price_history_property
            FOREIGN KEY (property_id) REFERENCES public.properties(property_id);
        """))
        
        # Индексы для ускорения запросов
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_transactions_property_id ON public.transactions(property_id);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_transactions_date ON public.transactions(date);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_price_history_property_id ON public.price_history(property_id);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_price_history_change_date ON public.price_history(change_date);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_properties_type ON public.properties(property_type);"))
    
    print("Загрузка данных успешно завершена!")


if __name__ == "__main__":
    load_csv_to_db()