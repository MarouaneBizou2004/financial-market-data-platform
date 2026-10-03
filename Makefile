.PHONY: help install ingest validate transform load dbt ml test dashboard docker-up docker-down

help:
	@echo "Financial Market Data Platform Commands:"
	@echo "  make install     - Install Python dependencies"
	@echo "  make ingest      - Ingest authentic market data (Bronze layer)"
	@echo "  make validate    - Validate integrity & build Silver layer"
	@echo "  make transform   - Execute Spark Window transformations (Gold layer)"
	@echo "  make load        - Load Star Schema relational data warehouse"
	@echo "  make dbt         - Execute dbt staging, intermediate, and marts models"
	@echo "  make ml          - Train and evaluate Market Regime ML model"
	@echo "  make test        - Run automated pytest suite"
	@echo "  make dashboard   - Launch Streamlit analytics dashboard"
	@echo "  make pipeline    - Run full end-to-end pipeline"
	@echo "  make docker-up   - Start PostgreSQL, Spark, and Airflow containers"
	@echo "  make docker-down - Stop Docker containers"

install:
	pip install -r requirements.txt

ingest:
	python src/ingestion/market_data.py

validate:
	python src/validation/market_checks.py

transform:
	python src/transformations/spark_transform.py

load:
	python src/utils/database.py

dbt:
	python src/transformations/dbt_runner.py

ml:
	python src/ml/train.py

test:
	python -m pytest -v

dashboard:
	streamlit run dashboards/app.py

pipeline:
	python main.py

docker-up:
	docker compose up -d

docker-down:
	docker compose down
