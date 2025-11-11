# PiazzaTi Deployment Guide

## CI/CD Workflow

Il deployment avviene automaticamente tramite GitHub Actions quando si fa push sul branch `main`.

### Processo di Deploy

1. **Test & Build**: 
   - Test backend (pytest)
   - Test build frontend (npm run build)
   - Build immagine backend Docker e push al registry Scaleway

2. **Deploy**:
   - Connessione SSH al server Scaleway
   - Git pull del codice aggiornato
   - Update nginx config da `deploy/nginx_piazzati_parse_grafana_home.conf`
   - Rebuild completo dell'immagine frontend via Docker
   - Restart di tutti i servizi

### File di Configurazione

- `docker-compose.yml` - Configurazione servizi principale
- `docker-compose.deploy.yml` - Override per production (generato automaticamente)
- `deploy/nginx_piazzati_parse_grafana_home.conf` - Configurazione nginx per il server

### Architettura Deploy

```
GitHub Push → CI/CD → Scaleway Server
    ↓           ↓           ↓
  Tests     Docker Build   Docker Compose
            Backend Push   Frontend Rebuild
                          Nginx Reload
```

### Servizi Deployati

- **Frontend** (porta 80): Home page + Parse SPA
- **Backend** (porta 8000): API FastAPI
- **PostgreSQL** (porta 5432): Database con pgvector
- **Ollama** (porta 11434): LLM service
- **Grafana** (porta 3000): Monitoring dashboards
- **Prometheus** (porta 9090): Metrics collection

### Monitoring

- Health checks automatici per tutti i servizi
- Logs accessibili via `docker compose logs <service>`
- Grafana dashboards per metriche sistema e applicazione

### Correzioni Recenti

- ✅ Fixed nginx proxy_pass per preservare il path `/api`
- ✅ Unified frontend build process via Docker
- ✅ Corrected home link in parser UI
- ✅ Sincronizzata nginx config tra sviluppo e produzione