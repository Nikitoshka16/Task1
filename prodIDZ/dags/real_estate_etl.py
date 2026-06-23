from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta

default_args = {
    'owner': 'admin',
    'depends_on_past': False,
    'start_date': datetime(2023, 1, 1),
    'retries': 1,
    'retry_delay': timedelta(minutes=1),
}

with DAG(
    dag_id='real_estate_etl',
    default_args=default_args,
    description='Конвейер: Генерация данных недвижимости -- Загрузка в БД -- Расчет витрины -- Визуализация',
    schedule_interval='@daily',
    catchup=False,
    tags=['real_estate', 'properties', 'transactions', 'bigdata'],
) as dag:

    task_generate_data = BashOperator(
        task_id='generate_data',
        bash_command='python /opt/airflow/scripts/generate_data.py',
    )

    task_load_raw = BashOperator(
        task_id='load_raw',
        bash_command='python /opt/airflow/scripts/load_raw.py',
    )

    task_create_mart = BashOperator(
        task_id='create_mart',
        bash_command='python /opt/airflow/scripts/create_mart.py',
    )

    task_create_visualizations = BashOperator(
        task_id='create_visualizations',
        bash_command='python /opt/airflow/scripts/visualize.py',
    )

    task_generate_data >> task_load_raw >> task_create_mart >> task_create_visualizations