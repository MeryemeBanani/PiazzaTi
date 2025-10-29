# Rollback procedure

Questo file spiega come usare lo script `scripts/remote_rollback.sh` per ripristinare
una versione precedente del backend su server.

Prerequisiti
- Accedere via SSH all'istanza (es. `ssh root@<IP>`)
- Avere `docker` e `docker compose` installati sul server
- Avere privilegi di root o sudo

Uso rapido

1. Eseguire lo script passando il tag (ad es. SHA) dell'immagine che vuoi deployare:

```bash
sudo bash /opt/piazzati/scripts/remote_rollback.sh <tag> --yes
```

2. Lo script creerà un `docker-compose.rollback.yml` che punta all'immagine completa
   `rg.nl-ams.scw.cloud/piazzati/backend/piazzati-backend:<tag>`, farà `docker pull` con
   retry, e poi `docker compose up -d` senza rebuild.

3. Lo script aspetta che l'endpoint `/health` risponda con successo (timeout 120s), e
   registra il tag attuale in `/var/lib/piazzati/last_deployed_tag` e un log in
   `/var/lib/piazzati/deploy_history.log`.

Note operative
- Lo script richiede il tag (es. SHA) come argomento. Se non passi il tag, stampa il
  valore corrente di `/var/lib/piazzati/last_deployed_tag`.
- Per rollback non interattivo (es. scriptato) passa `--yes` come secondo argomento.
- Se il registry è privato, accertati di essere loggato (`docker login`) o aggiungi il
  login manuale prima di eseguire lo script.

Esempio

```bash
ssh root@51.158.245.19
sudo bash /opt/piazzati/scripts/remote_rollback.sh 0123456 --yes
```

Questo comando ripristina l'immagine `rg.nl-ams.scw.cloud/piazzati/backend/piazzati-backend:0123456`.
