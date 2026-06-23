"""
Модуль для генерации синтетических данных по недвижимости.

Генерируемые сущности:
- Владельцы (300)
- Объекты недвижимости (2000)
- Ценовой архив (по 2-3 записи на объект)
- Сделки (150)

Выходные CSV-файлы:
- owners.csv
- properties.csv
- price_history.csv
- transactions.csv
"""

import pandas as pd
import random
import json
from faker import Faker
from datetime import datetime
import os

# Константы
N_OWNERS = 300
N_PROPERTIES = 2000
N_TRANSACTIONS = 150
DATA_DIR = '/opt/airflow/data'

# Создаём директорию для данных
os.makedirs(DATA_DIR, exist_ok=True)

# Инициализация генератора
fake = Faker('ru_RU')
Faker.seed(42)
random.seed(42)


def generate_owners(n: int) -> pd.DataFrame:
    """Генерация владельцев"""
    owners = []
    for i in range(1, n + 1):
        passport_series = random.randint(1000, 9999)
        passport_number = random.randint(100000, 999999)
        owners.append({
            'owner_id': i,
            'full_name': fake.name(),
            'passport_series': passport_series,
            'passport_number': passport_number,
            'passport_issued_by': fake.company(),
            'address': fake.address().replace('\n', ', '),
            'phone': fake.phone_number(),
            'email': fake.email()
        })
    return pd.DataFrame(owners)


def generate_properties(n: int, owner_ids: list) -> pd.DataFrame:
    """Генерация объектов недвижимости"""
    property_types = ['Квартира', 'Дом', 'Коммерческое']
    properties = []
    
    for i in range(1, n + 1):
        num_owners = random.choices([1, 2, 3], weights=[0.7, 0.2, 0.1])[0]
        selected_owners = random.sample(owner_ids, num_owners)
        
        if num_owners == 1:
            shares = [1.0]
        else:
            shares = []
            remaining = 1.0
            for j in range(num_owners - 1):
                share = round(random.uniform(0.1, remaining - 0.1), 2)
                shares.append(share)
                remaining -= share
            shares.append(round(remaining, 2))
        
        owners_with_shares = []
        for k in range(num_owners):
            owners_with_shares.append({
                'owner_id': selected_owners[k],
                'share': shares[k]
            })
        
        owner_info_json = json.dumps(owners_with_shares, ensure_ascii=False)
        
        properties.append({
            'property_id': i,
            'address': fake.address().replace('\n', ', '),
            'property_type': random.choice(property_types),
            'area': round(random.uniform(20.0, 200.0), 1),
            'rooms': random.randint(1, 5),
            'floor': random.randint(1, 25),
            'build_year': random.randint(1950, 2024),
            'cadastral_number': f"{random.randint(10, 99)}:{random.randint(10, 99)}:{random.randint(100000, 999999)}:{random.randint(1, 999)}",
            'owner_info': owner_info_json
        })
    
    return pd.DataFrame(properties)


def generate_price_history(properties_df: pd.DataFrame) -> pd.DataFrame:
    """Генерация ценового архива"""
    history = []
    record_id = 1
    start_date = datetime(2015, 1, 1)
    end_date = datetime.now()
    
    for _, prop in properties_df.iterrows():
        prop_id = prop['property_id']
        base_price = random.randint(1_000_000, 20_000_000)
        
        num_changes = random.choices([0, 1, 2, 3], weights=[0.3, 0.4, 0.2, 0.1])[0]
        change_dates = sorted([fake.date_between(start_date=start_date, end_date=end_date)
                               for _ in range(num_changes)])
        
        all_dates = [start_date.date()] + change_dates
        all_prices = [base_price]
        for _ in range(num_changes):
            change = random.uniform(-0.15, 0.25)
            new_price = int(all_prices[-1] * (1 + change))
            all_prices.append(new_price)
        
        for i in range(len(all_dates)):
            history.append({
                'price_history_id': record_id,
                'property_id': prop_id,
                'change_date': all_dates[i],
                'new_price': all_prices[i]
            })
            record_id += 1
    return pd.DataFrame(history)


def generate_transactions(n: int, properties_df: pd.DataFrame, owners_df: pd.DataFrame) -> pd.DataFrame:
    """Генерация сделок"""
    transactions = []
    for i in range(1, n + 1):
        property_row = properties_df.sample(1).iloc[0]
        property_id = property_row['property_id']
        current_owners = json.loads(property_row['owner_info'])
        seller_id = random.choice(current_owners)['owner_id']
        other_owners = owners_df[owners_df['owner_id'] != seller_id]['owner_id'].tolist()
        buyer_id = random.choice(other_owners)
        
        transaction_date = fake.date_between(start_date='-5y', end_date='today')
        price = random.randint(500_000, 30_000_000)
        
        transactions.append({
            'transaction_id': i,
            'date': transaction_date,
            'property_id': property_id,
            'seller_id': seller_id,
            'buyer_id': buyer_id,
            'price': price,
            'notary': fake.name()
        })
    return pd.DataFrame(transactions)


def main():
    print("Генерация данных о недвижимости...")
    
    print(f"  Генерация {N_OWNERS} владельцев...")
    owners_df = generate_owners(N_OWNERS)
    
    print(f"  Генерация {N_PROPERTIES} объектов недвижимости...")
    properties_df = generate_properties(N_PROPERTIES, owners_df['owner_id'].tolist())
    
    print(f"  Генерация ценового архива...")
    price_history_df = generate_price_history(properties_df)
    
    print(f"  Генерация {N_TRANSACTIONS} сделок...")
    transactions_df = generate_transactions(N_TRANSACTIONS, properties_df, owners_df)
    
    # Сохранение CSV
    owners_df.to_csv(f'{DATA_DIR}/owners.csv', index=False)
    properties_df.to_csv(f'{DATA_DIR}/properties.csv', index=False)
    price_history_df.to_csv(f'{DATA_DIR}/price_history.csv', index=False)
    transactions_df.to_csv(f'{DATA_DIR}/transactions.csv', index=False)
    
    print(f"Генерация завершена! Файлы сохранены в {DATA_DIR}")
    print(f"  - owners.csv: {len(owners_df)} записей")
    print(f"  - properties.csv: {len(properties_df)} записей")
    print(f"  - price_history.csv: {len(price_history_df)} записей")
    print(f"  - transactions.csv: {len(transactions_df)} записей")


if __name__ == "__main__":
    main()