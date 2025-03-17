from datetime import timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator 
from airflow.utils.dates import days_ago
import pandas as pd
import requests
import mysql.connector
import os


default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': days_ago(5),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=1),
}


ingestion_dag = DAG(
    'weather_ingestion',
    default_args=default_args,
    description='Fetch and load weather data into MySQL database',
    schedule_interval=timedelta(minutes=1),  
    catchup=False,
)


key = '7ac290a1f34eec96e26d09d25b47423b'
cities = ['Stockholm', 'London', 'New York', 'Tokyo', 'Sydney']

def transform_data():
    def fetch_weather_data(city):
        url = f'https://api.openweathermap.org/data/2.5/weather?q={city}&appid={key}'
        response = requests.get(url)
        return response.json()

    cities_responses = []
    for city in cities:
        data = fetch_weather_data(city)
        city_weather = {'city': city}
        city_weather.update(data['main']) 
        cities_responses.append(city_weather)

   
    df = pd.DataFrame(cities_responses)
    df.to_csv('/Users/yellow/Desktop/data_engineering/airflow_weather_01/weather_data.csv', index=False)  


task_1 = PythonOperator(
    task_id='transform_data',
    python_callable=transform_data,
    dag=ingestion_dag,
)


def load_data():

    df = pd.read_csv('/Users/yellow/Desktop/data_engineering/airflow_weather_01/weather_data.csv')


    connection = mysql.connector.connect(
        host='localhost',
        user='root',
        password='62686268nB@',
        database='weather'
    )
    cursor = connection.cursor()

 
    create_table_query = """
    CREATE TABLE IF NOT EXISTS weather_data_bahram(
        city VARCHAR(100),
        temp DECIMAL(5,2),
        feels_like DECIMAL(5,2),
        temp_min DECIMAL(5,2),
        temp_max DECIMAL(5,2),
        pressure INT,
        humidity INT,
        sea_level INT,
        grnd_level INT
    );
    """
    cursor.execute(create_table_query)


    for _, row in df.iterrows():
        cursor.execute("""
            INSERT INTO weather_data_bahram (city, temp, feels_like, temp_min, temp_max, pressure, humidity, sea_level, grnd_level)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, tuple(row))

    connection.commit()
    cursor.close()
    connection.close()

task_2 = PythonOperator(
    task_id='load_data',
    python_callable=load_data,
    dag=ingestion_dag,
)


task_1 >> task_2
schedule_interval=timedelta(minutes=1)  
