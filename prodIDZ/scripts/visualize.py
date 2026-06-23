import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sqlalchemy import create_engine
from dotenv import load_dotenv

load_dotenv('/opt/airflow/scripts/.env')

def create_visualizations():
    """Создание всех визуализаций для отчета"""
    
    host=os.getenv('DB_HOST', 'localhost')
    port=os.getenv('DB_PORT', '5432')
    database=os.getenv('DB_NAME', 'real_estate_db')
    user=os.getenv('DB_USER', 'admin')
    password=os.getenv('DB_PASSWORD', 'admin')
    
    engine = create_engine(f'postgresql://{user}:{password}@{host}:{port}/{database}')
    
    viz_dir = '/opt/airflow/visualizations'
    os.makedirs(viz_dir, exist_ok=True)
    
    # Настройка стиля
    plt.style.use('seaborn-v0_8-darkgrid')
    
    print("Начинаем создание визуализаций...")
    
    # ==================== ГРАФИК 1: Цены за кв.м по районам ====================
    try:
        df_map = pd.read_sql("""
            SELECT district, avg_price_per_sqm, total_deals
            FROM mart.real_estate_stats
            WHERE avg_price_per_sqm IS NOT NULL
            ORDER BY avg_price_per_sqm DESC
            LIMIT 15
        """, engine)
        
        if len(df_map) > 0:
            plt.figure(figsize=(12, 8))
            colors = plt.cm.RdYlGn_r(df_map['avg_price_per_sqm'] / df_map['avg_price_per_sqm'].max())
            bars = plt.barh(df_map['district'], df_map['avg_price_per_sqm'], color=colors)
            
            plt.xlabel('Средняя цена за кв.м (руб.)', fontsize=12)
            plt.ylabel('Район', fontsize=12)
            plt.title('Средняя цена за квадратный метр по районам (топ-15)', fontsize=14, fontweight='bold')
            
            for bar, val, deals in zip(bars, df_map['avg_price_per_sqm'], df_map['total_deals']):
                plt.text(val + 5000, bar.get_y() + bar.get_height()/2, 
                        f'{val:,.0f} руб.\n({deals} сделок)', va='center', fontsize=9)
            
            plt.tight_layout()
            plt.savefig(os.path.join(viz_dir, 'price_per_sqm_by_district.png'), dpi=150, bbox_inches='tight')
            plt.close()
            print("График 1 создан: price_per_sqm_by_district.png")
        else:
            print("Нет данных для графика 1")
    except Exception as e:
        print(f"Ошибка при создании графика 1: {e}")
    
    # ==================== ГРАФИК 2: Динамика цен по кварталам ====================
    try:
        df_dynamics = pd.read_sql("""
            WITH deals_with_date AS (
                SELECT
                    t.price / NULLIF(p.area, 0) AS price_per_sqm,
                    DATE_TRUNC('quarter', t.date::timestamp) AS quarter_start,
                    p.property_type
                FROM public.transactions t
                JOIN public.properties p ON t.property_id = p.property_id
                WHERE t.date IS NOT NULL AND p.area > 0
            )
            SELECT
                quarter_start,
                property_type,
                AVG(price_per_sqm) AS avg_price_per_sqm
            FROM deals_with_date
            WHERE quarter_start IS NOT NULL
            GROUP BY quarter_start, property_type
            ORDER BY quarter_start, property_type
        """, engine)
        
        if len(df_dynamics) > 0:
            plt.figure(figsize=(14, 7))
            for prop_type in df_dynamics['property_type'].unique():
                df_subset = df_dynamics[df_dynamics['property_type'] == prop_type]
                plt.plot(df_subset['quarter_start'], df_subset['avg_price_per_sqm'],
                        marker='o', linewidth=2, markersize=6, label=prop_type)
            
            plt.xlabel('Квартал', fontsize=12)
            plt.ylabel('Средняя цена за кв.м (руб.)', fontsize=12)
            plt.title('Динамика цен на недвижимость по кварталам', fontsize=14, fontweight='bold')
            plt.legend(loc='best')
            plt.grid(True, alpha=0.3)
            plt.xticks(rotation=45)
            plt.gca().yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x/1000:.0f}K'))
            
            plt.tight_layout()
            plt.savefig(os.path.join(viz_dir, 'price_dynamics_by_quarter.png'), dpi=150, bbox_inches='tight')
            plt.close()
            print("График 2 создан: price_dynamics_by_quarter.png")
        else:
            print("Нет данных для графика 2")
    except Exception as e:
        print(f"Ошибка при создании графика 2: {e}")
    
    # ==================== ГРАФИК 3: Сделки по типам недвижимости ====================
    try:
        df_by_type = pd.read_sql("""
            SELECT 
                property_type,
                SUM(total_deals) as total_deals
            FROM mart.real_estate_stats
            GROUP BY property_type
            ORDER BY total_deals DESC
        """, engine)
        
        if len(df_by_type) > 0:
            plt.figure(figsize=(10, 6))
            bars = plt.bar(df_by_type['property_type'], df_by_type['total_deals'], 
                          color=['#FF6B6B', '#4ECDC4', '#45B7D1'])
            
            plt.xlabel('Тип недвижимости', fontsize=12)
            plt.ylabel('Количество сделок', fontsize=12)
            plt.title('Количество сделок по типам недвижимости', fontsize=14, fontweight='bold')
            
            for bar, val in zip(bars, df_by_type['total_deals']):
                plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 5,
                        str(int(val)), ha='center', va='bottom', fontsize=11, fontweight='bold')
            
            plt.tight_layout()
            plt.savefig(os.path.join(viz_dir, 'deals_by_property_type.png'), dpi=150, bbox_inches='tight')
            plt.close()
            print("✓ График 3 создан: deals_by_property_type.png")
        else:
            print("Нет данных для графика 3")
    except Exception as e:
        print(f"Ошибка при создании графика 3: {e}")
    
# ==================== ГРАФИК 4: Boxplot цен по районам ====================
    try:
        df_boxplot = pd.read_sql("""
            SELECT
                CASE
                    WHEN address LIKE 'г.%%' THEN 
                        TRIM(SUBSTRING(address FROM 'г\\. ([^,]+)'))
                    WHEN address LIKE 'к.%%' THEN 
                        TRIM(SUBSTRING(address FROM 'к\\. ([^,]+)'))
                    WHEN address LIKE 'п.%%' THEN 
                        TRIM(SUBSTRING(address FROM 'п\\. ([^,]+)'))
                    ELSE 'Другой'
                END AS district,
                t.price
            FROM public.transactions t
            JOIN public.properties p ON t.property_id = p.property_id
        """, engine)
        
        if len(df_boxplot) > 0:
            # Убираем 'Другой' и берем топ-10 районов
            df_boxplot = df_boxplot[df_boxplot['district'] != 'Другой']
            top_districts = df_boxplot.groupby('district').size().nlargest(10).index
            df_filtered = df_boxplot[df_boxplot['district'].isin(top_districts)]
            
            plt.figure(figsize=(14, 8))
            sns.boxplot(data=df_filtered, x='district', y='price', palette='Set3')
            
            plt.xlabel('Район', fontsize=12)
            plt.ylabel('Цена сделки (руб.)', fontsize=12)
            plt.title('Распределение цен сделок по районам (топ-10)', fontsize=14, fontweight='bold')
            plt.xticks(rotation=45, ha='right')
            
            # Форматирование оси Y в миллионах
            plt.gca().yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x/1e6:.1f}M'))
            
            plt.tight_layout()
            plt.savefig(os.path.join(viz_dir, 'price_boxplot_by_district.png'), 
                       dpi=150, bbox_inches='tight')
            plt.close()
            print("График 4 создан: price_boxplot_by_district.png")
        else:
            print("Нет данных для графика 4")
    except Exception as e:
        print(f"Ошибка при создании графика 4: {e}")
    
    print(f"\n Создание визуализаций завершено! Графики сохранены в {viz_dir}")

if __name__ == "__main__":
    create_visualizations()