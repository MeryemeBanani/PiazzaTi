# =============================================================================
# PIAZZATI - GUIDA DEPLOYMENT SCALEWAY STEP-BY-STEP
# =============================================================================
# Procedura completa per deployment enterprise su Scaleway Cloud Platform
# =============================================================================

FASE 1: SETUP ACCOUNT SCALEWAY
===============================

1.1 REGISTRAZIONE E VERIFICA ACCOUNT
------------------------------------
□ Vai su https://console.scaleway.com
□ Registra account o effettua login
□ Verifica email e numero telefono
□ Aggiungi metodo di pagamento (carta di credito)
□ Attiva billing per utilizzo servizi

1.2 CREAZIONE PROJECT
---------------------
□ Nel dashboard Scaleway, vai su "Organization"
□ Clicca "Create Project"
□ Nome: "PiazzaTi Production"
□ Descrizione: "Production deployment for PiazzaTi platform"
□ Conferma creazione
□ Annotare PROJECT_ID (formato: 11111111-2222-3333-4444-555555555555)

1.3 GENERAZIONE API KEYS
------------------------
□ Vai su "IAM" → "API Keys"
□ Clicca "Generate API Key"
□ Nome: "PiazzaTi CI/CD Key"
□ Scope: "All resources" (o specifico per project)
□ Annotare:
  - ACCESS_KEY (formato: SCWXXXXXXXXXXXXXXXXX)
  - SECRET_KEY (formato: 11111111-2222-3333-4444-555555555555)

1.4 INSTALLAZIONE SCALEWAY CLI (LOCALE)
---------------------------------------
# Windows (PowerShell)
curl -o scw.exe https://github.com/scaleway/scaleway-cli/releases/latest/download/scw-windows-x86_64.exe
# Sposta in PATH o usa direttamente

# Linux/Mac
curl -o scw https://github.com/scaleway/scaleway-cli/releases/latest/download/scw-linux-x86_64
chmod +x scw
sudo mv scw /usr/local/bin/

# Verifica installazione
scw version

1.5 CONFIGURAZIONE CLI
----------------------
scw config set access-key=SCWXXXXXXXXXXXXXXXXX
scw config set secret-key=11111111-2222-3333-4444-555555555555
scw config set default-project-id=11111111-2222-3333-4444-555555555555
scw config set default-zone=fr-par-1
scw config set default-region=fr-par

# Test configurazione
scw account project list

===============================
FASE 2: SETUP SERVIZI MANAGED
===============================

2.1 CONTAINER REGISTRY
----------------------
□ Vai su "Container Registry"
□ Clicca "Create namespace"
□ Nome: "piazzati" 
□ Privacy: "Private"
□ Regione: "Paris (fr-par)"
□ Conferma creazione
□ Registry URL: rg.fr-par.scw.cloud/piazzati

2.2 MANAGED DATABASE POSTGRESQL
-------------------------------
□ Vai su "Managed Databases"
□ Clicca "Create Database Instance"
□ Engine: "PostgreSQL 15"
□ Node type: "DB-DEV-S" (development) o "DB-GP-XS" (production)
□ Nome: "piazzati-db-prod"
□ Database: "db_piazzati"
□ Username: "piazzati_user"
□ Password: [Genera password sicura 32 caratteri]
□ Backup automatici: Abilitati
□ Maintenance window: "Sunday 03:00-04:00"
□ Conferma creazione (5-10 minuti)
□ Annotare connection string completa

2.3 MANAGED REDIS (OPZIONALE)
-----------------------------
□ Vai su "Managed Databases"
□ Clicca "Create Redis Instance"  
□ Node type: "REDIS-DEV-S"
□ Nome: "piazzati-redis-prod"
□ Conferma creazione
□ Annotare connection URL

2.4 OBJECT STORAGE
------------------
□ Vai su "Object Storage"
□ Clicca "Create bucket"
□ Nome bucket: "piazzati-backups"
□ Regione: "fr-par"
□ Classe storage: "Standard"
□ Visibilità: "Private"
□ Versioning: "Enabled"
□ Conferma creazione

□ Crea secondo bucket:
□ Nome: "piazzati-uploads"
□ Stesse configurazioni

2.5 S3 CREDENTIALS
------------------
□ Vai su "IAM" → "API Keys" 
□ Clicca "Generate API Key"
□ Nome: "PiazzaTi S3 Access"
□ Scope: "ObjectStorageFullAccess"
□ Annotare S3_ACCESS_KEY e S3_SECRET_KEY

===============================
FASE 3: CONFIGURAZIONE DNS
===============================

3.1 DOMINIO E DNS
-----------------
□ Acquista dominio (es: piazzati.yourdomain.com)
□ Configura DNS provider (Cloudflare, Route53, etc.)
□ Crea record A temporanei (aggiornare dopo Load Balancer):
  - piazzati.yourdomain.com → 1.1.1.1 (temporaneo)
  - api.piazzati.yourdomain.com → 1.1.1.1 (temporaneo)  
  - grafana.piazzati.yourdomain.com → 1.1.1.1 (temporaneo)

===============================
FASE 4: GITHUB SECRETS
===============================

4.1 CONFIGURAZIONE REPOSITORY SECRETS
-------------------------------------
□ Vai su GitHub repository: https://github.com/MeryemeBanani/PiazzaTi
□ Settings → Secrets and variables → Actions
□ Clicca "New repository secret"

Aggiungi questi 6 secrets:

SCALEWAY_ACCESS_KEY:
SCWXXXXXXXXXXXXXXXXX

SCALEWAY_SECRET_KEY:
11111111-2222-3333-4444-555555555555

SCALEWAY_PROJECT_ID:
11111111-2222-3333-4444-555555555555

SCALEWAY_REGISTRY_USERNAME:
nologin

SCALEWAY_REGISTRY_PASSWORD:
11111111-2222-3333-4444-555555555555

SCALEWAY_DATABASE_URL:
postgresql://piazzati_user:PASSWORD@IP:5432/db_piazzati?sslmode=require

4.2 VERIFICA SECRETS
--------------------
□ Verifica che tutti i 6 secrets siano presenti
□ Controlla che non ci siano spazi extra
□ Test GitHub Actions pipeline

===============================
FASE 5: BUILD E DEPLOY

===============================

5.1 PRIMO DEPLOYMENT
--------------------
□ Commit e push modifiche su branch main:

git add .
git commit -m "feat: Production deployment configuration"
git push origin main

□ Vai su GitHub → Actions
□ Verifica che il workflow "CI/CD Pipeline" si avvii automaticamente
□ Monitora i 3 job:
  - test (PostgreSQL + linting + Docker build)
  - build-and-deploy (solo se su main branch)
  - security-scan (solo su PR)

5.2 VERIFICA DEPLOYMENT
-----------------------
□ Vai su Scaleway Console → "Container"
□ Verifica che container "piazzati-backend-prod" sia running
□ Controlla logs per errori
□ Testa health endpoint: curl http://CONTAINER_IP:8000/health

5.3 TROUBLESHOOTING DEPLOY
--------------------------
Se deployment fallisce:

# Check container logs
scw container container list
scw container container logs CONTAINER_ID

# Check image nel registry
scw container registry list

# Manual deployment se necessario
scw container container deploy \
  registry-image=rg.fr-par.scw.cloud/piazzati/piazzati-backend:latest \
  name=piazzati-backend-prod \
  port=8000

===============================
FASE 6: LOAD BALANCER E SSL
===============================

6.1 SETUP AUTOMATICO
--------------------
□ Sul tuo PC locale, configura environment:

export SCALEWAY_ACCESS_KEY="SCWXXXXXXXXXXXXXXXXX"
export SCALEWAY_SECRET_KEY="11111111-2222-3333-4444-555555555555"
export SCALEWAY_PROJECT_ID="11111111-2222-3333-4444-555555555555"

□ Esegui script setup HTTPS:

chmod +x ./scripts/setup-https.sh
./scripts/setup-https.sh

□ Script creerà:
  - Load Balancer enterprise
  - SSL certificate (self-signed per test)
  - Backend pools con health checks
  - Frontend rules HTTPS/HTTP redirect

6.2 AGGIORNAMENTO DNS
--------------------
□ Prendi IP Load Balancer dall'output script
□ Aggiorna record DNS:
  - piazzati.yourdomain.com → IP_LOAD_BALANCER
  - api.piazzati.yourdomain.com → IP_LOAD_BALANCER
  - grafana.piazzati.yourdomain.com → IP_LOAD_BALANCER

□ Attendi propagazione DNS (5-60 minuti)

6.3 SSL CERTIFICATE REALE
-------------------------
□ Per production, sostituire self-signed certificate:

# Let's Encrypt certificate
sudo certbot certonly --standalone \
  -d piazzati.yourdomain.com \
  -d api.piazzati.yourdomain.com \
  -d grafana.piazzati.yourdomain.com

# Upload su Scaleway Load Balancer
scw lb certificate update CERT_ID \
  certificate-chain="$(cat /etc/letsencrypt/live/piazzati.yourdomain.com/fullchain.pem)" \
  private-key="$(cat /etc/letsencrypt/live/piazzati.yourdomain.com/privkey.pem)"

===============================
FASE 7: CONFIGURAZIONE ENV PRODUCTION
===============================

7.1 AGGIORNAMENTO .env.prod
---------------------------
□ Modifica file .env.prod con valori reali:

DATABASE_URL=postgresql://piazzati_user:REAL_PASSWORD@REAL_DB_HOST:5432/db_piazzati?sslmode=require
REDIS_URL=redis://REAL_REDIS_HOST:6379/0
SCALEWAY_S3_ACCESS_KEY=REAL_S3_ACCESS_KEY
SCALEWAY_S3_SECRET_KEY=REAL_S3_SECRET_KEY
SECRET_KEY=[Genera con: openssl rand -base64 32]
GRAFANA_ADMIN_PASSWORD=[Password sicura]

7.2 DEPLOY CON ENV PRODUCTION
-----------------------------
□ Aggiorna container con nuove variabili:

# Se hai file .env.prod locale
scw container container update piazzati-backend-prod \
  --environment-variables-file .env.prod

# O manualmente via console Scaleway

===============================
FASE 8: MONITORING STACK
===============================

8.1 DEPLOY GRAFANA E PROMETHEUS
-------------------------------
□ Deploy stack completo con monitoring:

# Deploy production stack
docker-compose -f docker-compose.prod.yml up -d

# Deploy con security hardening
docker-compose -f docker-compose.prod.yml -f docker-compose.security.yml up -d

8.2 CONFIGURAZIONE GRAFANA
--------------------------
□ Accedi: https://grafana.piazzati.yourdomain.com:3000
□ Login: admin / [password da .env.prod]
□ Cambia password default
□ Import dashboard da configs/
□ Configura data sources
□ Test alerting rules

===============================
FASE 9: BACKUP SYSTEM
===============================

9.1 CONFIGURAZIONE BACKUP
-------------------------
□ Configura environment per backup:

export SCALEWAY_S3_ACCESS_KEY="your_s3_key"
export SCALEWAY_S3_SECRET_KEY="your_s3_secret"
export DATABASE_URL="your_database_url"
export GRAFANA_ADMIN_PASSWORD="your_grafana_password"

□ Test backup manuale:

./scripts/backup-system.sh manual

9.2 SETUP BACKUP AUTOMATICI
---------------------------
□ Installa crontab per backup automatici:

crontab configs/backup-crontab

□ Crea directory log:

sudo mkdir -p /var/log/piazzati
sudo chown $USER:$USER /var/log/piazzati

□ Monitora backup:

tail -f /var/log/piazzati/backup.log

===============================
FASE 10: SECURITY HARDENING
===============================

10.1 ESECUZIONE SECURITY SCRIPT
-------------------------------
□ Esegui script sicurezza:

chmod +x ./scripts/security-hardening.sh
./scripts/security-hardening.sh

□ Script configurerà:
  - Security Groups Scaleway
  - Grafana password sicure
  - Database security
  - SSL certificates
  - Security monitoring

10.2 CONFIGURAZIONE MANUALE
---------------------------
□ Vai su Scaleway Console → "Security Groups"
□ Verifica regole firewall create
□ Aggiungi il tuo IP admin per SSH access
□ Testa connessioni applicazione

===============================
FASE 11: TESTING E VALIDATION
===============================

11.1 HEALTH CHECKS
------------------
□ API Health: curl https://api.piazzati.yourdomain.com/health
□ Grafana: https://grafana.piazzati.yourdomain.com:3000
□ Metrics: https://api.piazzati.yourdomain.com/metrics (internal)
□ SSL test: https://www.ssllabs.com/ssltest/

11.2 PERFORMANCE TESTING
------------------------
□ Load testing:

# Test rate limiting
for i in {1..100}; do curl https://api.piazzati.yourdomain.com/health; done

# Test response times
curl -w "@curl-format.txt" -o /dev/null -s https://api.piazzati.yourdomain.com/health

11.3 SECURITY TESTING
---------------------
□ Security headers: curl -I https://api.piazzati.yourdomain.com
□ SSL configuration: nmap --script ssl-enum-ciphers -p 443 piazzati.yourdomain.com
□ Rate limiting: Test burst requests
□ Authentication: Test API endpoints

===============================
FASE 12: GO LIVE!
===============================

12.1 FINAL CHECKLIST
--------------------
□ ✅ Database running e accessibile
□ ✅ Container deployed e healthy
□ ✅ Load Balancer configured con SSL
□ ✅ DNS pointing correttamente
□ ✅ Monitoring dashboard functional
□ ✅ Backup system operational
□ ✅ Security hardening applied
□ ✅ Performance testing passed

12.2 POST-DEPLOYMENT
--------------------
□ Monitor application logs
□ Check database performance
□ Verify backup execution
□ Monitor security alerts
□ Setup alerting notifications
□ Document production credentials (securely)

===============================
TROUBLESHOOTING COMUNE
===============================

PROBLEMA: Container non si avvia
SOLUZIONE: 
- Check logs: scw container container logs CONTAINER_ID
- Verify environment variables
- Check database connectivity

PROBLEMA: DNS non resolve
SOLUZIONE:
- Verify DNS propagation: nslookup piazzati.yourdomain.com
- Check TTL settings
- Clear DNS cache

PROBLEMA: SSL certificate errori
SOLUZIONE:
- Verify certificate chain completeness
- Check domain names in certificate
- Ensure Load Balancer certificate upload

PROBLEMA: Database connection failed
SOLUZIONE:
- Check database status: scw rdb instance list
- Verify connection string format
- Check security group rules

PROBLEMA: Backup failures
SOLUZIONE:
- Verify S3 credentials
- Check bucket permissions
- Test manual backup script

===============================
CONTATTI SUPPORT
===============================

- Scaleway Support: Enterprise ticket system
- GitHub Issues: https://github.com/MeryemeBanani/PiazzaTi/issues
- Documentation: README.md e DOCUMENTAZIONE.txt

===============================
SUCCESS! 🎉
===============================

La tua applicazione PiazzaTi è ora live su:
- Main: https://piazzati.yourdomain.com  
- API: https://api.piazzati.yourdomain.com
- Grafana: https://grafana.piazzati.yourdomain.com:3000

Buon deployment! 🚀