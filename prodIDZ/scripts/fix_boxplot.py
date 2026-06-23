import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sqlalchemy import create_engine
from dotenv import load_dotenv

load_dotenv('/opt/airflow/scripts/.env')

host=os.getenv('DB_HOST', 'localhost'),
port=os.getenv('DB_PORT', '5432'),
database=os.getenv('DB_NAME', 'real_estate_db'),
user=os.getenv('DB_USER', 'admin'),
password=os.getenv('DB_PASSWORD', 'admin')

engine = create_engine(f'postgresql://{user}:{password}@{host}:{port}/{database}')
viz_dir = '/opt/airflow/visualizations'
os.makedirs(viz_dir, exist_ok=True)

# Получаем данные
query = """
SELECT 
    p.address,
    t.price
FROM public.transactions t
JOIN public.properties p ON t.property_id = p.property_id
"""

df = pd.read_sql(query, engine)

# Правильная функция извлечения района из адреса
def extract_district(address):
    if not isinstance(address, str):
        return 'Другой'
    
    # Префиксы и соответствующие им паттерны
    # После префикса идёт название населённого пункта до первой запятой
    prefixes = ['г.', 'к.', 'п.', 'д.', 'с.', 'ст.', 'клх ']
    
    for prefix in prefixes:
        if address.startswith(prefix):
            # Находим название после префикса
            rest = address[len(prefix):].strip()
            # Берём всё до запятой или пробела с номером дома
            # Название может быть: "Устюжна", "Горячий Ключ" и т.д.
            import re
            # Ищем название: буквы, пробелы, дефисы, но не цифры
            match = re.match(r'^([А-Яа-яЁё\s\-]+?)(?:,|\s+[д\.,])', rest)
            if match:
                return match.group(1).strip()
            # Если не нашли по сложному паттерну, берём первое слово
            first_word = rest.split(',')[0].split()[0]
            return first_word
    
    return 'Другой'

df['district'] = df['address'].apply(extract_district)

# Отфильтровываем 'Другой' и пустые значения
df = df[df['district'] != 'Другой']
df = df[df['district'].notna()]
df = df[df['district'] != '']

print(f"Найдено районов: {df['district'].nunique()}")
print("Примеры районов:", df['district'].unique()[:15])

# Берем топ-10 районов по количеству сделок
top_districts = df.groupby('district').size().nlargest(10).index
df_filtered = df[df['district'].isin(top_districts)]

print(f"Топ-10 районов: {list(top_districts)}")
print(f"Количество сделок в топ-10: {df_filtered.groupby('district').size().to_dict()}")

# Создаем boxplot
plt.figure(figsize=(14, 8))
sns.boxplot(data=df_filtered, x='district', y='price', palette='Set3')

plt.xlabel('Район', fontsize=12)
plt.ylabel('Цена сделки (руб.)', fontsize=12)
plt.title('Распределение цен сделок по районам (топ-10)', fontsize=14, fontweight='bold')
plt.xticks(rotation=45, ha='right')

# Форматирование оси Y
plt.gca().yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x/1e6:.1f}M'))

plt.tight_layout()
plt.savefig(os.path.join(viz_dir, 'price_boxplot_by_district.png'), dpi=150, bbox_inches='tight')
plt.close()

print("График 4 создан: price_boxplot_by_district.png")