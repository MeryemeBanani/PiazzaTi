# PiazzaTi Production Deployment Makefile
# Comandi semplificati per gestione ambiente produzione

.PHONY: help build deploy deploy-backend stop logs clean backup restore

# Variables
COMPOSE_FILE = docker-compose.prod.yml
ENV_FILE = .env.prod
PROJECT_NAME = piazzati-prod

help: ## Mostra questo help
	@echo "PiazzaTi Production Deployment Commands:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

setup: ## Setup iniziale ambiente produzione
	@echo "🔧 Setup ambiente produzione..."
	@cp .env.example $(ENV_FILE) 2>/dev/null || echo "$(ENV_FILE) already exists"
	@echo "✅ Modifica $(ENV_FILE) con le tue configurazioni Scaleway"
	@mkdir -p /opt/piazzati/data/{prometheus,grafana,redis}
	@mkdir -p /opt/piazzati/logs/nginx
	@mkdir -p nginx/ssl

build: ## Build tutte le immagini
	@echo "🏗️ Building immagini produzione..."
	docker-compose -f $(COMPOSE_FILE) --env-file $(ENV_FILE) build

deploy: ## Deploy stack completo in produzione
	@echo "🚀 Deploying stack completo..."
	docker-compose -f $(COMPOSE_FILE) --env-file $(ENV_FILE) --project-name $(PROJECT_NAME) up -d
	@echo "✅ Stack deployato!"
	@make status

deploy-backend: ## Deploy solo backend (per CI/CD)
	@echo "🔄 Aggiornamento backend..."
	docker-compose -f $(COMPOSE_FILE) --env-file $(ENV_FILE) --project-name $(PROJECT_NAME) up -d piazzati-backend
	@echo "✅ Backend aggiornato!"

deploy-monitoring: ## Deploy solo stack monitoring
	@echo "📊 Deploying monitoring stack..."
	docker-compose -f $(COMPOSE_FILE) --env-file $(ENV_FILE) --project-name $(PROJECT_NAME) up -d prometheus grafana node-exporter cadvisor
	@echo "✅ Monitoring deployato!"

deploy-with-db: ## Deploy con database self-hosted
	@echo "🗄️ Deploying con database self-hosted..."
	docker-compose -f $(COMPOSE_FILE) --env-file $(ENV_FILE) --project-name $(PROJECT_NAME) --profile self-hosted-db up -d
	@echo "✅ Stack completo con DB deployato!"

deploy-with-redis: ## Deploy con Redis cache
	@echo "💾 Deploying con Redis..."
	docker-compose -f $(COMPOSE_FILE) --env-file $(ENV_FILE) --project-name $(PROJECT_NAME) --profile with-redis up -d
	@echo "✅ Stack con Redis deployato!"

scale-backend: ## Scale backend a 3 istanze
	@echo "📈 Scaling backend..."
	docker-compose -f $(COMPOSE_FILE) --env-file $(ENV_FILE) --project-name $(PROJECT_NAME) up -d --scale piazzati-backend=3
	@echo "✅ Backend scalato a 3 istanze!"

stop: ## Ferma tutti i servizi
	@echo "⏹️ Stopping services..."
	docker-compose -f $(COMPOSE_FILE) --env-file $(ENV_FILE) --project-name $(PROJECT_NAME) down
	@echo "✅ Servizi fermati!"

restart: ## Riavvia tutti i servizi
	@echo "🔄 Riavvio servizi..."
	docker-compose -f $(COMPOSE_FILE) --env-file $(ENV_FILE) --project-name $(PROJECT_NAME) restart
	@echo "✅ Servizi riavviati!"

status: ## Mostra status servizi
	@echo "📊 Status servizi:"
	@docker-compose -f $(COMPOSE_FILE) --env-file $(ENV_FILE) --project-name $(PROJECT_NAME) ps
	@echo ""
	@echo "🌐 URLs disponibili:"
	@echo "  API Health: https://api.piazzati.scaleway.example/health"
	@echo "  Grafana: https://grafana.piazzati.scaleway.example"
	@echo "  Prometheus: https://prometheus.piazzati.scaleway.example"

logs: ## Mostra logs di tutti i servizi
	@echo "📝 Logs servizi:"
	docker-compose -f $(COMPOSE_FILE) --env-file $(ENV_FILE) --project-name $(PROJECT_NAME) logs -f

logs-backend: ## Mostra logs solo backend
	@echo "📝 Logs backend:"
	docker-compose -f $(COMPOSE_FILE) --env-file $(ENV_FILE) --project-name $(PROJECT_NAME) logs -f piazzati-backend

logs-grafana: ## Mostra logs Grafana
	@echo "📝 Logs Grafana:"
	docker-compose -f $(COMPOSE_FILE) --env-file $(ENV_FILE) --project-name $(PROJECT_NAME) logs -f grafana

health: ## Controlla health di tutti i servizi
	@echo "🏥 Health check servizi:"
	@curl -s -o /dev/null -w "Backend: %{http_code}\n" https://api.piazzati.scaleway.example/health || echo "Backend: DOWN"
	@curl -s -o /dev/null -w "Grafana: %{http_code}\n" https://grafana.piazzati.scaleway.example/api/health || echo "Grafana: DOWN"
	@curl -s -o /dev/null -w "Prometheus: %{http_code}\n" https://prometheus.piazzati.scaleway.example/-/healthy || echo "Prometheus: DOWN"

backup: ## Backup dati (Grafana, Prometheus)
	@echo "💾 Backup dati..."
	@mkdir -p backups/$(shell date +%Y%m%d_%H%M%S)
	@docker cp piazzati-grafana-prod:/var/lib/grafana backups/$(shell date +%Y%m%d_%H%M%S)/grafana
	@docker cp piazzati-prometheus-prod:/prometheus backups/$(shell date +%Y%m%d_%H%M%S)/prometheus
	@echo "✅ Backup completato in backups/$(shell date +%Y%m%d_%H%M%S)/"

restore: ## Restore da backup (specificare BACKUP_DIR=path)
	@echo "🔄 Restore da $(BACKUP_DIR)..."
	@docker cp $(BACKUP_DIR)/grafana piazzati-grafana-prod:/var/lib/
	@docker cp $(BACKUP_DIR)/prometheus piazzati-prometheus-prod:/
	@make restart
	@echo "✅ Restore completato!"

clean: ## Pulizia completa (ATTENZIONE: elimina tutto!)
	@echo "🗑️ Pulizia completa..."
	@read -p "Sei sicuro? Questo eliminerà TUTTI i dati (y/N): " confirm && [ "$$confirm" = "y" ]
	docker-compose -f $(COMPOSE_FILE) --env-file $(ENV_FILE) --project-name $(PROJECT_NAME) down -v --remove-orphans
	docker system prune -f
	@echo "✅ Pulizia completata!"

ssl-cert: ## Genera certificati SSL self-signed (per test)
	@echo "🔒 Generazione certificati SSL self-signed..."
	@mkdir -p nginx/ssl
	openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
		-keyout nginx/ssl/key.pem \
		-out nginx/ssl/cert.pem \
		-subj "/C=FR/ST=IDF/L=Paris/O=PiazzaTi/OU=IT/CN=piazzati.scaleway.example"
	@echo "✅ Certificati generati in nginx/ssl/"

update: ## Aggiorna tutte le immagini
	@echo "🔄 Aggiornamento immagini..."
	docker-compose -f $(COMPOSE_FILE) --env-file $(ENV_FILE) --project-name $(PROJECT_NAME) pull
	@make deploy
	@echo "✅ Immagini aggiornate!"

monitor: ## Apri monitoring dashboard
	@echo "📊 Aprendo dashboard di monitoring..."
	@echo "Grafana: https://grafana.piazzati.scaleway.example"
	@echo "Prometheus: https://prometheus.piazzati.scaleway.example"

# Development helpers
dev-setup: ## Setup ambiente sviluppo locale
	@echo "🛠️ Setup ambiente sviluppo..."
	docker-compose up -d
	@echo "✅ Ambiente dev pronto su localhost!"

prod-check: ## Verifica configurazione produzione
	@echo "✅ Controllo configurazione produzione..."
	@test -f $(ENV_FILE) || (echo "❌ $(ENV_FILE) non trovato!" && exit 1)
	@test -f nginx/ssl/cert.pem || (echo "⚠️ Certificati SSL non trovati - esegui 'make ssl-cert'" && exit 1)
	@echo "✅ Configurazione OK!"