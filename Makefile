.PHONY: help install init-db start stop logs clean api web deploy dev dev-stop dev-status

help: ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

deploy: ## One-click deployment (Docker)
	@bash deploy.sh

dev: ## Start all services locally for debugging
	@bash dev.sh start

dev-stop: ## Stop all local services
	@bash dev.sh stop

dev-status: ## Show local service status
	@bash dev.sh status

dev-logs: ## Show local service logs (usage: make dev-logs SVC=api)
	@bash dev.sh logs $(SVC)

install: ## Install dependencies
	pip install -e ".[dev]"

start: ## Start Neo4j and Redis
	docker-compose up -d
	@echo "Waiting for services to start..."
	@sleep 5
	@echo "Neo4j Web UI: http://localhost:7474"
	@echo "Neo4j Bolt: bolt://localhost:7687"

stop: ## Stop all services
	docker-compose down

logs: ## Show service logs
	docker-compose logs -f

init-db: ## Initialize Neo4j schema
	python scripts/init_neo4j.py

api: ## Start FastAPI server
	uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload

web: ## Start Streamlit web UI
	streamlit run web/streamlit_app.py --server.port 8501

clean: ## Clean up data and logs
	rm -rf data/raw/* data/processed/* data/embeddings/* logs/*

test: ## Run tests
	pytest tests/ -v

lint: ## Run linter
	ruff check src/ tests/
	ruff format --check src/ tests/

format: ## Format code
	ruff format src/ tests/

typecheck: ## Run type checker
	mypy src/

ingest: ## Ingest a document (usage: make ingest FILE=path/to/doc.pdf)
	python scripts/ingest_document.py $(FILE)

query: ## Query the knowledge graph (usage: make query Q="your question")
	python scripts/query.py $(Q)

benchmark: ## Run performance benchmark
	python scripts/benchmark.py -b all -n 10

people-import: ## Import sample people data
	python scripts/import_people.py

people-graph: ## Start people graph visualization
	streamlit run web/people_graph.py --server.port 8502

admin: ## Start admin management interface
	streamlit run web/admin.py --server.port 8503

jobgraph-import: ## Import sample job data
	python scripts/import_jobs.py

jobgraph-generate: ## Generate and import sample data (usage: make jobgraph-generate COUNT=50)
	python3 scripts/import_generated.py --companies $(or $(COUNT),50)

crawl-data: ## Crawl data from public sources
	python3 scripts/crawl_data.py

import-data: ## Import crawled data to Neo4j
	python3 scripts/import_to_neo4j.py

jobgraph: ## Start JobGraph web UI (求职图谱)
	streamlit run web/jobgraph.py --server.port 8504
