# python/pipelines/daily_fetch.py

from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta

from data.retrieval import fetch_stock_data, save_data_to_db

default_args = {
    'owner': 'airflow',
    'start_date': datetime(2025, 4, 1),
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

with DAG(
    dag_id='daily_stock_fetch',
    default_args=default_args,
    schedule_interval='@daily',
    catchup=False,
) as dag:

    def fetch_and_store(ticker: str):
        df = fetch_stock_data(ticker, period='1y', interval='1d')
        save_data_to_db(df, ticker)

    task_aapl = PythonOperator(
        task_id='fetch_AAPL',
        python_callable=fetch_and_store,
        op_kwargs={'ticker': 'AAPL'},
    )

    task_msft = PythonOperator(
        task_id='fetch_MSFT',
        python_callable=fetch_and_store,
        op_kwargs={'ticker': 'MSFT'},
    )

    task_aapl >> task_msft