from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.empty import EmptyOperator
from airflow.operators.python import PythonOperator

def print_task_name(task_name):
    print(f"Executing task: {task_name}")

default_args = {
    'owner': 'data_engineer',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

# Define the DAG
with DAG(
    '01_dag_dependency_resolver',
    default_args=default_args,
    description='A simple DAG demonstrating dependency resolution',
    schedule_interval=timedelta(days=1),
    start_date=datetime(2023, 1, 1),
    catchup=False,
    tags=['example'],
) as dag:

    # Define tasks
    task_a = PythonOperator(task_id='task_A', python_callable=print_task_name, op_kwargs={'task_name': 'A'})
    task_b = PythonOperator(task_id='task_B', python_callable=print_task_name, op_kwargs={'task_name': 'B'})
    task_c = PythonOperator(task_id='task_C', python_callable=print_task_name, op_kwargs={'task_name': 'C'})
    task_d = PythonOperator(task_id='task_D', python_callable=print_task_name, op_kwargs={'task_name': 'D'})
    task_e = PythonOperator(task_id='task_E', python_callable=print_task_name, op_kwargs={'task_name': 'E'})

    # Define dependencies (A -> [B, C] -> D -> E)
    task_a >> [task_b, task_c] >> task_d >> task_e

if __name__ == "__main__":
    # In a real environment, Airflow parses this file. 
    # For local testing of the DAG structure, you can run:
    dag.test()
