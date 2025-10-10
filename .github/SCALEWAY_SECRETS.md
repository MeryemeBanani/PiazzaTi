# Scaleway Secrets Configuration

Per configurare il deployment automatico su Scaleway, aggiungi questi secrets nel repository GitHub:

## Repository Settings → Secrets and variables → Actions

### 1. Scaleway Container Registry
```
SCALEWAY_REGISTRY_USERNAME = nologin
SCALEWAY_REGISTRY_PASSWORD = <your-scaleway-registry-token>
```

### 2. Scaleway API Credentials
```
SCALEWAY_ACCESS_KEY = <your-scaleway-access-key>
SCALEWAY_SECRET_KEY = <your-scaleway-secret-key>
SCALEWAY_PROJECT_ID = <your-scaleway-project-id>
```

### 3. Database Configuration
```
SCALEWAY_DATABASE_URL = postgresql://username:password@hostname:port/database
```

## Come ottenere le credenziali:

### Container Registry Token:
1. Vai su [Scaleway Console](https://console.scaleway.com/)
2. Container Registry → Settings → Credentials
3. Genera un nuovo token
4. Username: `nologin`
5. Password: il token generato

### API Credentials:
1. Vai su [Scaleway Console](https://console.scaleway.com/)
2. Project → API Keys
3. Crea una nuova API Key
4. Copia Access Key, Secret Key e Project ID

### Managed Database:
1. Vai su [Scaleway Console](https://console.scaleway.com/)
2. Managed Databases → PostgreSQL
3. Crea un nuovo database PostgreSQL
4. Copia l'URL di connessione

## Configurazione Container Registry

Crea il namespace nel Container Registry:
```bash
# Installa Scaleway CLI
curl -o scw https://github.com/scaleway/scaleway-cli/releases/latest/download/scw-linux-x86_64
chmod +x scw

# Configura CLI
scw config set access-key=<access-key>
scw config set secret-key=<secret-key>
scw config set default-project-id=<project-id>

# Crea namespace
scw registry namespace create name=piazzati region=fr-par
```

## Test del workflow

Il workflow si attiva automaticamente su:
- Push su branch `main` → Deploy automatico
- Pull Request → Test e security scan
- Push su branch `dev` o `feature/*` → Solo test

## Monitoraggio Deployment

Una volta configurato, puoi monitorare:
- GitHub Actions: Build status e logs
- Scaleway Console: Container status e metrics  
- Container logs: `scw container container logs <container-id>`