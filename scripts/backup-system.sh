#!/bin/bash

# =============================================================================
# SCALEWAY OBJECT STORAGE BACKUP SYSTEM
# =============================================================================
# Backup automatico di PostgreSQL, Grafana dashboards e Prometheus data
# Usage: ./scripts/backup-system.sh [manual|restore]
# =============================================================================

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
BACKUP_TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_DIR="/tmp/piazzati-backup-$BACKUP_TIMESTAMP"
S3_BUCKET="piazzati-backups"
S3_ENDPOINT="https://s3.fr-par.scw.cloud"
RETENTION_DAYS=30

# Scaleway Object Storage configuration
if [ -z "$SCALEWAY_S3_ACCESS_KEY" ] || [ -z "$SCALEWAY_S3_SECRET_KEY" ]; then
    echo -e "${RED}Error: Missing Scaleway S3 credentials${NC}"
    echo "Set environment variables:"
    echo "export SCALEWAY_S3_ACCESS_KEY=your_access_key"
    echo "export SCALEWAY_S3_SECRET_KEY=your_secret_key"
    exit 1
fi

echo -e "${BLUE}==============================================================================${NC}"
echo -e "${BLUE}PIAZZATI - SCALEWAY OBJECT STORAGE BACKUP SYSTEM${NC}"
echo -e "${BLUE}==============================================================================${NC}"

# Function: Database backup
backup_database() {
    echo -e "${YELLOW}[1/4] Creating PostgreSQL backup...${NC}"
    
    if [ -z "$DATABASE_URL" ]; then
        echo -e "${RED}Error: DATABASE_URL not set${NC}"
        exit 1
    fi
    
    mkdir -p "$BACKUP_DIR/database"
    
    # Full database dump
    pg_dump "$DATABASE_URL" \
        --verbose \
        --clean \
        --if-exists \
        --create \
        --format=custom \
        --file="$BACKUP_DIR/database/piazzati_full_$BACKUP_TIMESTAMP.dump"
    
    # Schema-only backup
    pg_dump "$DATABASE_URL" \
        --schema-only \
        --verbose \
        --file="$BACKUP_DIR/database/piazzati_schema_$BACKUP_TIMESTAMP.sql"
    
    # Data-only backup
    pg_dump "$DATABASE_URL" \
        --data-only \
        --verbose \
        --file="$BACKUP_DIR/database/piazzati_data_$BACKUP_TIMESTAMP.sql"
    
    echo -e "${GREEN}✅ Database backup completed${NC}"
}

# Function: Grafana backup
backup_grafana() {
    echo -e "${YELLOW}[2/4] Creating Grafana backup...${NC}"
    
    mkdir -p "$BACKUP_DIR/grafana"
    
    # Check if Grafana container is running
    if docker compose ps grafana | grep -q "Up"; then
        # Backup Grafana data directory
        docker compose exec -T grafana tar -czf - /var/lib/grafana | cat > "$BACKUP_DIR/grafana/grafana_data_$BACKUP_TIMESTAMP.tar.gz"
        
        # Backup Grafana configuration
        docker compose exec -T grafana cat /etc/grafana/grafana.ini > "$BACKUP_DIR/grafana/grafana.ini"
        
        # Export dashboards via API
        if [ ! -z "$GRAFANA_ADMIN_PASSWORD" ]; then
            mkdir -p "$BACKUP_DIR/grafana/dashboards"
            
            # Get all dashboard UIDs
            DASHBOARD_UIDS=$(curl -s -u "admin:$GRAFANA_ADMIN_PASSWORD" \
                "http://localhost:3000/api/search?type=dash-db" | \
                jq -r '.[].uid')
            
            # Export each dashboard
            for uid in $DASHBOARD_UIDS; do
                curl -s -u "admin:$GRAFANA_ADMIN_PASSWORD" \
                    "http://localhost:3000/api/dashboards/uid/$uid" | \
                    jq '.dashboard' > "$BACKUP_DIR/grafana/dashboards/$uid.json"
            done
            
            echo -e "${GREEN}✅ Grafana dashboards exported${NC}"
        else
            echo -e "${YELLOW}⚠️  GRAFANA_ADMIN_PASSWORD not set, skipping dashboard export${NC}"
        fi
    else
        echo -e "${YELLOW}⚠️  Grafana container not running, skipping Grafana backup${NC}"
    fi
    
    echo -e "${GREEN}✅ Grafana backup completed${NC}"
}

# Function: Prometheus backup
backup_prometheus() {
    echo -e "${YELLOW}[3/4] Creating Prometheus backup...${NC}"
    
    mkdir -p "$BACKUP_DIR/prometheus"
    
    # Check if Prometheus container is running
    if docker compose ps prometheus | grep -q "Up"; then
        # Backup Prometheus data directory
        docker compose exec -T prometheus tar -czf - /prometheus | cat > "$BACKUP_DIR/prometheus/prometheus_data_$BACKUP_TIMESTAMP.tar.gz"
        
        # Backup Prometheus configuration
        docker compose exec -T prometheus cat /etc/prometheus/prometheus.yml > "$BACKUP_DIR/prometheus/prometheus.yml"
        
        # Backup alert rules
        if docker compose exec -T prometheus ls /etc/prometheus/alert-rules.yml 2>/dev/null; then
            docker compose exec -T prometheus cat /etc/prometheus/alert-rules.yml > "$BACKUP_DIR/prometheus/alert-rules.yml"
        fi
    else
        echo -e "${YELLOW}⚠️  Prometheus container not running, skipping Prometheus backup${NC}"
    fi
    
    echo -e "${GREEN}✅ Prometheus backup completed${NC}"
}

# Function: Upload to Scaleway Object Storage
upload_to_s3() {
    echo -e "${YELLOW}[4/4] Uploading backup to Scaleway Object Storage...${NC}"
    
    # Configure AWS CLI for Scaleway
    export AWS_ACCESS_KEY_ID="$SCALEWAY_S3_ACCESS_KEY"
    export AWS_SECRET_ACCESS_KEY="$SCALEWAY_S3_SECRET_KEY"
    
    # Create backup archive
    cd /tmp
    tar -czf "piazzati-backup-$BACKUP_TIMESTAMP.tar.gz" "piazzati-backup-$BACKUP_TIMESTAMP/"
    
    # Upload to S3
    aws s3 cp "piazzati-backup-$BACKUP_TIMESTAMP.tar.gz" \
        "s3://$S3_BUCKET/backups/piazzati-backup-$BACKUP_TIMESTAMP.tar.gz" \
        --endpoint-url="$S3_ENDPOINT"
    
    # Create backup metadata
    cat > "/tmp/backup-metadata-$BACKUP_TIMESTAMP.json" << EOF
{
    "timestamp": "$BACKUP_TIMESTAMP",
    "backup_type": "full",
    "components": ["database", "grafana", "prometheus"],
    "size_bytes": $(stat -c%s "piazzati-backup-$BACKUP_TIMESTAMP.tar.gz"),
    "retention_until": "$(date -d "+$RETENTION_DAYS days" +%Y-%m-%d)",
    "created_by": "backup-system.sh",
    "version": "1.0"
}
EOF
    
    # Upload metadata
    aws s3 cp "/tmp/backup-metadata-$BACKUP_TIMESTAMP.json" \
        "s3://$S3_BUCKET/metadata/backup-metadata-$BACKUP_TIMESTAMP.json" \
        --endpoint-url="$S3_ENDPOINT"
    
    # Cleanup local files
    rm -rf "$BACKUP_DIR"
    rm -f "/tmp/piazzati-backup-$BACKUP_TIMESTAMP.tar.gz"
    rm -f "/tmp/backup-metadata-$BACKUP_TIMESTAMP.json"
    
    echo -e "${GREEN}✅ Backup uploaded to s3://$S3_BUCKET/backups/piazzati-backup-$BACKUP_TIMESTAMP.tar.gz${NC}"
}

# Function: Cleanup old backups
cleanup_old_backups() {
    echo -e "${YELLOW}Cleaning up backups older than $RETENTION_DAYS days...${NC}"
    
    # List and delete old backups
    CUTOFF_DATE=$(date -d "-$RETENTION_DAYS days" +%Y%m%d)
    
    aws s3 ls "s3://$S3_BUCKET/backups/" --endpoint-url="$S3_ENDPOINT" | \
    while read -r line; do
        BACKUP_DATE=$(echo "$line" | awk '{print $4}' | grep -o '[0-9]\{8\}' | head -1)
        if [ ! -z "$BACKUP_DATE" ] && [ "$BACKUP_DATE" -lt "$CUTOFF_DATE" ]; then
            BACKUP_FILE=$(echo "$line" | awk '{print $4}')
            echo "Deleting old backup: $BACKUP_FILE"
            aws s3 rm "s3://$S3_BUCKET/backups/$BACKUP_FILE" --endpoint-url="$S3_ENDPOINT"
            
            # Delete corresponding metadata
            METADATA_FILE=$(echo "$BACKUP_FILE" | sed 's/piazzati-backup-/backup-metadata-/' | sed 's/.tar.gz/.json/')
            aws s3 rm "s3://$S3_BUCKET/metadata/$METADATA_FILE" --endpoint-url="$S3_ENDPOINT" 2>/dev/null || true
        fi
    done
    
    echo -e "${GREEN}✅ Cleanup completed${NC}"
}

# Function: List available backups
list_backups() {
    echo -e "${YELLOW}Available backups in Scaleway Object Storage:${NC}"
    echo ""
    
    aws s3 ls "s3://$S3_BUCKET/backups/" --endpoint-url="$S3_ENDPOINT" | \
    awk '{print $1" "$2" "$4" ("$3" bytes)"}' | \
    sort -r
}

# Function: Restore from backup
restore_backup() {
    local RESTORE_FILE="$1"
    
    if [ -z "$RESTORE_FILE" ]; then
        echo -e "${RED}Error: Please specify backup file to restore${NC}"
        echo "Usage: $0 restore <backup-filename>"
        list_backups
        exit 1
    fi
    
    echo -e "${YELLOW}Restoring from backup: $RESTORE_FILE${NC}"
    
    # Download backup
    RESTORE_DIR="/tmp/piazzati-restore-$(date +%s)"
    mkdir -p "$RESTORE_DIR"
    
    aws s3 cp "s3://$S3_BUCKET/backups/$RESTORE_FILE" \
        "$RESTORE_DIR/$RESTORE_FILE" \
        --endpoint-url="$S3_ENDPOINT"
    
    # Extract backup
    cd "$RESTORE_DIR"
    tar -xzf "$RESTORE_FILE"
    
    # Extract backup directory name
    BACKUP_FOLDER=$(tar -tzf "$RESTORE_FILE" | head -1 | cut -f1 -d"/")
    
    echo -e "${YELLOW}Backup extracted to: $RESTORE_DIR/$BACKUP_FOLDER${NC}"
    
    # Restore database
    if [ -f "$RESTORE_DIR/$BACKUP_FOLDER/database/piazzati_full_"*".dump" ]; then
        echo -e "${YELLOW}Restoring database...${NC}"
        DUMP_FILE=$(ls "$RESTORE_DIR/$BACKUP_FOLDER/database/piazzati_full_"*".dump")
        pg_restore --verbose --clean --if-exists --create -d "$DATABASE_URL" "$DUMP_FILE"
        echo -e "${GREEN}✅ Database restored${NC}"
    fi
    
    # Restore Grafana
    if [ -f "$RESTORE_DIR/$BACKUP_FOLDER/grafana/grafana_data_"*".tar.gz" ]; then
        echo -e "${YELLOW}Restoring Grafana data...${NC}"
        GRAFANA_BACKUP=$(ls "$RESTORE_DIR/$BACKUP_FOLDER/grafana/grafana_data_"*".tar.gz")
        
        # Stop Grafana
        docker compose stop grafana
        
        # Restore data
        docker compose run --rm grafana sh -c "rm -rf /var/lib/grafana/* && tar -xzf - -C /" < "$GRAFANA_BACKUP"
        
        # Restart Grafana
        docker compose up -d grafana
        
        echo -e "${GREEN}✅ Grafana data restored${NC}"
    fi
    
    # Restore Prometheus
    if [ -f "$RESTORE_DIR/$BACKUP_FOLDER/prometheus/prometheus_data_"*".tar.gz" ]; then
        echo -e "${YELLOW}Restoring Prometheus data...${NC}"
        PROMETHEUS_BACKUP=$(ls "$RESTORE_DIR/$BACKUP_FOLDER/prometheus/prometheus_data_"*".tar.gz")
        
        # Stop Prometheus
        docker compose stop prometheus
        
        # Restore data
        docker compose run --rm prometheus sh -c "rm -rf /prometheus/* && tar -xzf - -C /" < "$PROMETHEUS_BACKUP"
        
        # Restart Prometheus
        docker compose up -d prometheus
        
        echo -e "${GREEN}✅ Prometheus data restored${NC}"
    fi
    
    # Cleanup
    rm -rf "$RESTORE_DIR"
    
    echo -e "${GREEN}🎉 Backup restore completed!${NC}"
}

# Main execution
case "${1:-manual}" in
    "manual")
        backup_database
        backup_grafana
        backup_prometheus
        upload_to_s3
        cleanup_old_backups
        
        echo -e "${BLUE}==============================================================================${NC}"
        echo -e "${GREEN}🎉 Backup completed successfully!${NC}"
        echo -e "${BLUE}==============================================================================${NC}"
        echo -e "Backup file: ${GREEN}piazzati-backup-$BACKUP_TIMESTAMP.tar.gz${NC}"
        echo -e "Location: ${GREEN}s3://$S3_BUCKET/backups/${NC}"
        echo -e "Retention: ${YELLOW}$RETENTION_DAYS days${NC}"
        ;;
        
    "list")
        list_backups
        ;;
        
    "restore")
        restore_backup "$2"
        ;;
        
    "cleanup")
        cleanup_old_backups
        ;;
        
    *)
        echo "Usage: $0 [manual|list|restore <filename>|cleanup]"
        echo ""
        echo "Commands:"
        echo "  manual           - Create a manual backup (default)"
        echo "  list             - List available backups"
        echo "  restore <file>   - Restore from specific backup"
        echo "  cleanup          - Remove old backups"
        exit 1
        ;;
esac