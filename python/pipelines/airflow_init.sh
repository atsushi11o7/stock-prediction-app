export AIRFLOW_HOME=$(pwd)/.airflow

# Airflow のメタDB（SQLite）を初期化
airflow db init

# 管理者ユーザを作成
airflow users create \
  --username atsushi11o7 \
  --firstname Dev \
  --lastname User \
  --role Admin \
  --email admin@example.com