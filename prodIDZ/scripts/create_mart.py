import os
import psycopg2
from dotenv import load_dotenv

load_dotenv('/opt/airflow/scripts/.env')

def build_real_estate_mart():
    """Создает полную витрину mart.real_estate_stats со всеми полями"""
    print("Создаем полную витрину mart.real_estate_stats")
    conn = None
    
    try:
        conn = psycopg2.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            port=os.getenv('DB_PORT', '5432'),
            database=os.getenv('DB_NAME', 'real_estate_db'),
            user=os.getenv('DB_USER', 'admin'),
            password=os.getenv('DB_PASSWORD', 'admin')
        )
        conn.autocommit = False

        query = """
        CREATE SCHEMA IF NOT EXISTS mart;
        DROP TABLE IF EXISTS mart.real_estate_stats CASCADE;
        
        CREATE TABLE mart.real_estate_stats AS
        WITH properties_with_district AS (   --Извлечение района из адреса
            SELECT
                property_id,
                property_type,
                area,
                CASE
                    WHEN address LIKE 'г.%%' THEN TRIM(SUBSTRING(address FROM 'г\. ([^,]+)'))
                    WHEN address LIKE 'к.%%' THEN TRIM(SUBSTRING(address FROM 'к\. ([^,]+)'))
                    WHEN address LIKE 'п.%%' THEN TRIM(SUBSTRING(address FROM 'п\. ([^,]+)'))
                    WHEN address LIKE 'д.%%' THEN TRIM(SUBSTRING(address FROM 'д\. ([^,]+)'))
                    WHEN address LIKE 'с.%%' THEN TRIM(SUBSTRING(address FROM 'с\. ([^,]+)'))
                    WHEN address LIKE 'клх %%' THEN TRIM(SUBSTRING(address FROM 'клх ([^,]+)'))
                    ELSE 'Другой'
                END AS district
            FROM public.properties
        ),
        deals_with_price AS (  --Расчёт цены за квадратный метр
            SELECT
                pwd.district,
                p.property_type,
                t.price,
                t.price / NULLIF(p.area, 0) AS price_per_sqm,
                p.area,
                t.date,
                EXTRACT(YEAR FROM t.date::timestamp) * 4 + 
                EXTRACT(QUARTER FROM t.date::timestamp) AS quarter_num
            FROM public.transactions t
            JOIN public.properties p ON t.property_id = p.property_id
            JOIN properties_with_district pwd ON p.property_id = pwd.property_id
            WHERE pwd.district IS NOT NULL AND pwd.district != 'Другой'
        ),
        quarterly_avg AS (   --Средняя цена за квартал
            SELECT
                district,
                property_type,
                quarter_num,
                AVG(price_per_sqm) AS avg_price_per_sqm
            FROM deals_with_price
            GROUP BY district, property_type, quarter_num
        ),
        quarterly_with_change AS (  --Вычисление изменения цены за квартал
            SELECT
                q1.district,
                q1.property_type,
                q1.quarter_num,
                q1.avg_price_per_sqm,
                ((q1.avg_price_per_sqm - LAG(q1.avg_price_per_sqm) OVER ( --процент_изменения = (текущая_цена - предыдущая_цена)
                    PARTITION BY q1.district, q1.property_type        -- / предыдущая_цена × 100
                    ORDER BY q1.quarter_num
                )) / NULLIF(LAG(q1.avg_price_per_sqm) OVER (
                    PARTITION BY q1.district, q1.property_type 
                    ORDER BY q1.quarter_num
                ), 0)) * 100 AS price_change_quarter
            FROM quarterly_avg q1
        ),
        latest_change AS (   --Берём только последнее изменение
            SELECT DISTINCT ON (district, property_type)  --оставляет по одной строке для каждой уникальной пары
                district,
                property_type,
                price_change_quarter
            FROM quarterly_with_change
            WHERE price_change_quarter IS NOT NULL
            ORDER BY district, property_type, quarter_num DESC --берёт самый поздний квартал
        )
        SELECT --сборка витрины
            dwp.district,
            dwp.property_type,
            ROUND(CAST(AVG(dwp.price_per_sqm) AS NUMERIC), 0) AS avg_price_per_sqm, --Средняя цена за квадратный метр
            PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY dwp.price) AS median_price, --Медианная цена сделки
            COUNT(*) AS total_deals, --Количество сделок
            ROUND(CAST(AVG(dwp.area) AS NUMERIC), 1) AS avg_area, --Средняя площадь
            ROUND(CAST(lc.price_change_quarter AS NUMERIC), 2) AS price_change_quarter  --Изменение цены за квартал
        FROM deals_with_price dwp
        LEFT JOIN latest_change lc 
            ON dwp.district = lc.district 
            AND dwp.property_type = lc.property_type
        GROUP BY 
            dwp.district,
            dwp.property_type,
            lc.price_change_quarter;
        
        ALTER TABLE mart.real_estate_stats ADD PRIMARY KEY (district, property_type);
        """
        
        with conn.cursor() as cursor:
            cursor.execute(query)
            conn.commit()
            
            # Показываем количество записей в витрине
            cursor.execute("SELECT COUNT(*) FROM mart.real_estate_stats;")
            count = cursor.fetchone()[0]
            print(f"\n✓ Витрина mart.real_estate_stats успешно создана!")
            print(f"   Записей в витрине: {count}")
        
    except Exception as e:
        print(f"ОШИБКА: {e}")
        if conn:
            conn.rollback()
        raise e
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    build_real_estate_mart()