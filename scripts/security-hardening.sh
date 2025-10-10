#!/bin/bash

# =============================================================================
# PIAZZATI PRODUCTION SECURITY HARDENING SCRIPT
# =============================================================================
# Configurazione sicurezza enterprise per deployment Scaleway
# Usage: ./scripts/security-hardening.sh
# =============================================================================

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}==============================================================================${NC}"
echo -e "${BLUE}PIAZZATI - PRODUCTION SECURITY HARDENING${NC}"
echo -e "${BLUE}==============================================================================${NC}"

# Function: Generate secure passwords
generate_secure_password() {
    local length=${1:-32}
    openssl rand -base64 $length | tr -d "=+/" | cut -c1-$length
}

# Function: Update Grafana security
secure_grafana() {
    echo -e "${YELLOW}[1/6] Securing Grafana configuration...${NC}"
    
    # Generate secure passwords
    GRAFANA_ADMIN_PASSWORD=$(generate_secure_password 24)
    GRAFANA_SECRET_KEY=$(generate_secure_password 32)
    
    # Create secure Grafana environment
    cat > ./configs/grafana-security.env << EOF
# GRAFANA SECURITY CONFIGURATION
GF_SECURITY_ADMIN_USER=admin
GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_ADMIN_PASSWORD}
GF_SECURITY_SECRET_KEY=${GRAFANA_SECRET_KEY}

# Security Settings
GF_SECURITY_DISABLE_GRAVATAR=true
GF_SECURITY_DISABLE_BRUTE_FORCE_LOGIN_PROTECTION=false
GF_SECURITY_LOGIN_MAXIMUM_INACTIVE_LIFETIME_DURATION=7d
GF_SECURITY_LOGIN_MAXIMUM_LIFETIME_DURATION=30d
GF_SECURITY_COOKIE_SAMESITE=strict
GF_SECURITY_COOKIE_SECURE=true

# Authentication
GF_AUTH_DISABLE_LOGIN_FORM=false
GF_AUTH_DISABLE_SIGNOUT_MENU=false
GF_AUTH_ANONYMOUS_ENABLED=false

# Server Security
GF_SERVER_ENFORCE_DOMAIN=true
GF_SERVER_DOMAIN=grafana.piazzati.yourdomain.com
GF_SERVER_ROOT_URL=https://grafana.piazzati.yourdomain.com:3000
GF_SERVER_SERVE_FROM_SUB_PATH=false

# Content Security Policy
GF_SECURITY_CONTENT_TYPE_PROTECTION_HEADER=true
GF_SECURITY_X_CONTENT_TYPE_OPTIONS=nosniff
GF_SECURITY_X_XSS_PROTECTION=true
GF_SECURITY_STRICT_TRANSPORT_SECURITY=true
GF_SECURITY_STRICT_TRANSPORT_SECURITY_MAX_AGE_SECONDS=86400

# Database Security
GF_DATABASE_WAL=true
GF_DATABASE_CACHE_MODE=private

# Users & Organizations
GF_USERS_ALLOW_SIGN_UP=false
GF_USERS_ALLOW_ORG_CREATE=false
GF_USERS_AUTO_ASSIGN_ORG=true
GF_USERS_AUTO_ASSIGN_ORG_ROLE=Viewer
GF_USERS_DEFAULT_THEME=dark

# Logging Security
GF_LOG_MODE=file
GF_LOG_LEVEL=warn
GF_LOG_FILTERS=alerting.notifier:info
EOF

    echo -e "${GREEN}✅ Grafana security configuration created${NC}"
    echo -e "${YELLOW}   Admin password: ${GRAFANA_ADMIN_PASSWORD}${NC}"
    echo -e "${YELLOW}   Secret key: ${GRAFANA_SECRET_KEY}${NC}"
}

# Function: Create Scaleway Security Groups (Firewall)
create_security_groups() {
    echo -e "${YELLOW}[2/6] Creating Scaleway Security Groups...${NC}"
    
    if ! command -v scw &> /dev/null; then
        echo -e "${RED}Error: Scaleway CLI not found${NC}"
        return 1
    fi
    
    # Create security group for backend
    BACKEND_SG_ID=$(scw instance security-group create \
        name="piazzati-backend-sg" \
        description="Security group for PiazzaTi backend containers" \
        --output json | jq -r '.id')
    
    # Backend inbound rules
    scw instance security-group-rule create \
        security-group-id=$BACKEND_SG_ID \
        direction=inbound \
        action=accept \
        protocol=TCP \
        dest-port-from=8000 \
        dest-port-to=8000 \
        ip-range=172.16.0.0/12  # Private network only
    
    scw instance security-group-rule create \
        security-group-id=$BACKEND_SG_ID \
        direction=inbound \
        action=accept \
        protocol=TCP \
        dest-port-from=22 \
        dest-port-to=22 \
        ip-range=YOUR_ADMIN_IP/32  # Replace with admin IP
    
    # Create security group for database
    DATABASE_SG_ID=$(scw instance security-group create \
        name="piazzati-database-sg" \
        description="Security group for PiazzaTi database" \
        --output json | jq -r '.id')
    
    # Database inbound rules (PostgreSQL)
    scw instance security-group-rule create \
        security-group-id=$DATABASE_SG_ID \
        direction=inbound \
        action=accept \
        protocol=TCP \
        dest-port-from=5432 \
        dest-port-to=5432 \
        ip-range=172.16.0.0/12  # Private network only
    
    # Create security group for monitoring
    MONITORING_SG_ID=$(scw instance security-group create \
        name="piazzati-monitoring-sg" \
        description="Security group for PiazzaTi monitoring stack" \
        --output json | jq -r '.id')
    
    # Monitoring inbound rules
    scw instance security-group-rule create \
        security-group-id=$MONITORING_SG_ID \
        direction=inbound \
        action=accept \
        protocol=TCP \
        dest-port-from=3000 \
        dest-port-to=3000 \
        ip-range=0.0.0.0/0  # Grafana public access via Load Balancer
    
    scw instance security-group-rule create \
        security-group-id=$MONITORING_SG_ID \
        direction=inbound \
        action=accept \
        protocol=TCP \
        dest-port-from=9090 \
        dest-port-to=9090 \
        ip-range=172.16.0.0/12  # Prometheus private only
    
    echo -e "${GREEN}✅ Security groups created:${NC}"
    echo -e "   Backend SG: ${BACKEND_SG_ID}"
    echo -e "   Database SG: ${DATABASE_SG_ID}"
    echo -e "   Monitoring SG: ${MONITORING_SG_ID}"
}

# Function: SSL Certificate security
configure_ssl_security() {
    echo -e "${YELLOW}[3/6] Configuring SSL/TLS security...${NC}"
    
    mkdir -p ./ssl/production
    
    # Create SSL configuration
    cat > ./ssl/production/ssl-config.conf << EOF
[req]
default_bits = 4096
prompt = no
default_md = sha256
distinguished_name = dn
req_extensions = v3_req

[dn]
C=IT
ST=Italy
L=Milan
O=PiazzaTi
OU=IT Department
CN=piazzati.yourdomain.com

[v3_req]
basicConstraints = CA:FALSE
keyUsage = nonRepudiation, digitalSignature, keyEncipherment
subjectAltName = @alt_names

[alt_names]
DNS.1 = piazzati.yourdomain.com
DNS.2 = api.piazzati.yourdomain.com
DNS.3 = grafana.piazzati.yourdomain.com
DNS.4 = www.piazzati.yourdomain.com
EOF

    # Generate production-ready SSL certificate request
    openssl req -new -nodes -out ./ssl/production/piazzati.csr \
        -newkey rsa:4096 -keyout ./ssl/production/piazzati.key \
        -config ./ssl/production/ssl-config.conf
    
    # Generate self-signed for testing (replace with real cert)
    openssl x509 -req -days 365 -in ./ssl/production/piazzati.csr \
        -signkey ./ssl/production/piazzati.key \
        -out ./ssl/production/piazzati.crt \
        -extensions v3_req -extfile ./ssl/production/ssl-config.conf
    
    # Create certificate chain
    cat ./ssl/production/piazzati.crt > ./ssl/production/piazzati-chain.pem
    
    # Set secure permissions
    chmod 600 ./ssl/production/piazzati.key
    chmod 644 ./ssl/production/piazzati.crt
    chmod 644 ./ssl/production/piazzati-chain.pem
    
    echo -e "${GREEN}✅ SSL certificates configured${NC}"
    echo -e "${YELLOW}   Note: Replace self-signed cert with real CA certificate${NC}"
}

# Function: Database security hardening
secure_database() {
    echo -e "${YELLOW}[4/6] Configuring database security...${NC}"
    
    # Generate database passwords
    DB_USER_PASSWORD=$(generate_secure_password 32)
    DB_READONLY_PASSWORD=$(generate_secure_password 32)
    
    # Create database security script
    cat > ./scripts/database-security.sql << EOF
-- =============================================================================
-- PIAZZATI DATABASE SECURITY HARDENING
-- =============================================================================

-- Create application user with minimal privileges
CREATE USER IF NOT EXISTS piazzati_app WITH PASSWORD '${DB_USER_PASSWORD}';
CREATE USER IF NOT EXISTS piazzati_readonly WITH PASSWORD '${DB_READONLY_PASSWORD}';
CREATE USER IF NOT EXISTS piazzati_backup WITH PASSWORD '$(generate_secure_password 32)';

-- Create application database
CREATE DATABASE db_piazzati OWNER piazzati_app;

-- Connect to application database
\c db_piazzati;

-- Revoke default permissions
REVOKE ALL ON SCHEMA public FROM PUBLIC;
REVOKE ALL ON DATABASE db_piazzati FROM PUBLIC;

-- Grant minimal privileges to application user
GRANT CONNECT ON DATABASE db_piazzati TO piazzati_app;
GRANT USAGE ON SCHEMA public TO piazzati_app;
GRANT CREATE ON SCHEMA public TO piazzati_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO piazzati_app;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO piazzati_app;

-- Grant read-only access to monitoring user
GRANT CONNECT ON DATABASE db_piazzati TO piazzati_readonly;
GRANT USAGE ON SCHEMA public TO piazzati_readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO piazzati_readonly;

-- Grant backup privileges
GRANT CONNECT ON DATABASE db_piazzati TO piazzati_backup;
GRANT USAGE ON SCHEMA public TO piazzati_backup;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO piazzati_backup;

-- Set default privileges for future objects
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO piazzati_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT USAGE, SELECT ON SEQUENCES TO piazzati_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO piazzati_readonly;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO piazzati_backup;

-- Enable row level security (if needed)
-- ALTER TABLE your_table ENABLE ROW LEVEL SECURITY;

-- Create audit log table
CREATE TABLE IF NOT EXISTS audit_log (
    id SERIAL PRIMARY KEY,
    table_name VARCHAR(255) NOT NULL,
    operation VARCHAR(10) NOT NULL,
    old_values JSONB,
    new_values JSONB,
    user_name VARCHAR(255),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create audit trigger function
CREATE OR REPLACE FUNCTION audit_trigger_function()
RETURNS TRIGGER AS \$\$
BEGIN
    IF TG_OP = 'DELETE' THEN
        INSERT INTO audit_log (table_name, operation, old_values, user_name)
        VALUES (TG_TABLE_NAME, TG_OP, row_to_json(OLD), current_user);
        RETURN OLD;
    ELSIF TG_OP = 'UPDATE' THEN
        INSERT INTO audit_log (table_name, operation, old_values, new_values, user_name)
        VALUES (TG_TABLE_NAME, TG_OP, row_to_json(OLD), row_to_json(NEW), current_user);
        RETURN NEW;
    ELSIF TG_OP = 'INSERT' THEN
        INSERT INTO audit_log (table_name, operation, new_values, user_name)
        VALUES (TG_TABLE_NAME, TG_OP, row_to_json(NEW), current_user);
        RETURN NEW;
    END IF;
    RETURN NULL;
END;
\$\$ LANGUAGE plpgsql;

-- Security settings
ALTER SYSTEM SET log_statement = 'all';
ALTER SYSTEM SET log_min_duration_statement = 1000;
ALTER SYSTEM SET log_connections = on;
ALTER SYSTEM SET log_disconnections = on;
ALTER SYSTEM SET log_checkpoints = on;

-- Reload configuration
SELECT pg_reload_conf();
EOF

    echo -e "${GREEN}✅ Database security configuration created${NC}"
    echo -e "${YELLOW}   App user password: ${DB_USER_PASSWORD}${NC}"
    echo -e "${YELLOW}   Readonly password: ${DB_READONLY_PASSWORD}${NC}"
}

# Function: Application security configuration
secure_application() {
    echo -e "${YELLOW}[5/6] Configuring application security...${NC}"
    
    # Generate application secrets
    JWT_SECRET=$(generate_secure_password 48)
    API_KEY=$(generate_secure_password 32)
    
    # Create application security configuration
    cat > ./configs/app-security.env << EOF
# APPLICATION SECURITY CONFIGURATION
JWT_SECRET_KEY=${JWT_SECRET}
API_SECRET_KEY=${API_KEY}

# Security Headers
SECURITY_HSTS_MAX_AGE=31536000
SECURITY_CONTENT_TYPE_OPTIONS=nosniff
SECURITY_FRAME_OPTIONS=DENY
SECURITY_XSS_PROTECTION=1; mode=block
SECURITY_REFERRER_POLICY=strict-origin-when-cross-origin

# CORS Security
CORS_ALLOW_ORIGINS=https://piazzati.yourdomain.com,https://www.piazzati.yourdomain.com
CORS_ALLOW_CREDENTIALS=true
CORS_ALLOW_METHODS=GET,POST,PUT,DELETE,OPTIONS
CORS_ALLOW_HEADERS=Authorization,Content-Type,X-Requested-With

# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_REQUESTS_PER_MINUTE=60
RATE_LIMIT_REQUESTS_PER_HOUR=1000
RATE_LIMIT_REQUESTS_PER_DAY=10000

# Session Security
SESSION_COOKIE_SECURE=true
SESSION_COOKIE_HTTPONLY=true
SESSION_COOKIE_SAMESITE=strict
SESSION_TIMEOUT=3600

# File Upload Security
UPLOAD_MAX_SIZE=10485760
UPLOAD_ALLOWED_EXTENSIONS=pdf,doc,docx,txt,jpg,jpeg,png
UPLOAD_SCAN_VIRUS=true
UPLOAD_QUARANTINE_PATH=/var/quarantine

# API Security
API_VERSION_HEADER_REQUIRED=true
API_REQUEST_ID_HEADER=true
API_CORRELATION_ID_REQUIRED=false

# Logging Security
LOG_SENSITIVE_DATA=false
LOG_MAX_LENGTH=1000
LOG_SANITIZE_EMAILS=true
LOG_SANITIZE_TOKENS=true
EOF

    echo -e "${GREEN}✅ Application security configuration created${NC}"
    echo -e "${YELLOW}   JWT Secret: ${JWT_SECRET}${NC}"
    echo -e "${YELLOW}   API Key: ${API_KEY}${NC}"
}

# Function: Create security monitoring
setup_security_monitoring() {
    echo -e "${YELLOW}[6/6] Setting up security monitoring...${NC}"
    
    # Create fail2ban configuration
    cat > ./configs/fail2ban-piazzati.conf << EOF
[piazzati-auth]
enabled = true
port = 8000
protocol = tcp
filter = piazzati-auth
logpath = /var/log/piazzati/auth.log
maxretry = 5
bantime = 3600
findtime = 600
action = iptables-multiport[name=piazzati, port="8000,3000", protocol=tcp]

[piazzati-api]
enabled = true
port = 8000
protocol = tcp
filter = piazzati-api
logpath = /var/log/piazzati/api.log
maxretry = 20
bantime = 1800
findtime = 300
EOF

    # Create security alert rules for Prometheus
    cat > ./monitoring/security-alert-rules.yml << EOF
groups:
  - name: security_alerts
    rules:
      - alert: HighFailedLoginRate
        expr: increase(auth_failed_login_total[5m]) > 10
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: "High failed login rate detected"
          description: "More than 10 failed logins in the last 5 minutes"
      
      - alert: UnauthorizedAPIAccess
        expr: increase(http_requests_total{status=~"401|403"}[5m]) > 20
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "High unauthorized access attempts"
          description: "More than 20 unauthorized requests in 5 minutes"
      
      - alert: DatabaseConnectionFailure
        expr: increase(database_connection_errors_total[5m]) > 5
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Database connection failures"
          description: "Multiple database connection failures detected"
      
      - alert: SSLCertificateExpiring
        expr: ssl_certificate_expiry_days < 30
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "SSL certificate expiring soon"
          description: "SSL certificate will expire in less than 30 days"
      
      - alert: SecurityHeaderMissing
        expr: security_headers_check == 0
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Security headers missing"
          description: "Required security headers are not present in responses"
EOF

    echo -e "${GREEN}✅ Security monitoring configured${NC}"
}

# Save all credentials securely
save_credentials() {
    echo -e "${YELLOW}Saving credentials to secure location...${NC}"
    
    # Create credentials file (should be encrypted in production)
    cat > ./configs/production-credentials.txt << EOF
=============================================================================
PIAZZATI PRODUCTION CREDENTIALS
Generated: $(date)
=============================================================================

GRAFANA:
Admin User: admin
Admin Password: $(grep GF_SECURITY_ADMIN_PASSWORD ./configs/grafana-security.env | cut -d'=' -f2)
Secret Key: $(grep GF_SECURITY_SECRET_KEY ./configs/grafana-security.env | cut -d'=' -f2)

DATABASE:
App User Password: $(grep "piazzati_app WITH PASSWORD" ./scripts/database-security.sql | sed "s/.*PASSWORD '\(.*\)';/\1/")
Readonly Password: $(grep "piazzati_readonly WITH PASSWORD" ./scripts/database-security.sql | sed "s/.*PASSWORD '\(.*\)';/\1/")

APPLICATION:
JWT Secret: $(grep JWT_SECRET_KEY ./configs/app-security.env | cut -d'=' -f2)
API Key: $(grep API_SECRET_KEY ./configs/app-security.env | cut -d'=' -f2)

SCALEWAY SECURITY GROUPS:
Backend SG: ${BACKEND_SG_ID:-"Not created"}
Database SG: ${DATABASE_SG_ID:-"Not created"}  
Monitoring SG: ${MONITORING_SG_ID:-"Not created"}

=============================================================================
IMPORTANT: Store this file securely and delete after copying to password manager
=============================================================================
EOF

    chmod 600 ./configs/production-credentials.txt
    
    echo -e "${GREEN}✅ Credentials saved to ./configs/production-credentials.txt${NC}"
    echo -e "${RED}⚠️  IMPORTANT: Copy credentials to secure password manager and delete file${NC}"
}

# Main execution
echo -e "${YELLOW}Starting security hardening process...${NC}"

secure_grafana
create_security_groups
configure_ssl_security
secure_database
secure_application
setup_security_monitoring
save_credentials

echo -e "${BLUE}==============================================================================${NC}"
echo -e "${GREEN}🎉 SECURITY HARDENING COMPLETED SUCCESSFULLY!${NC}"
echo -e "${BLUE}==============================================================================${NC}"
echo ""
echo -e "${YELLOW}NEXT STEPS:${NC}"
echo "1. Copy credentials from ./configs/production-credentials.txt to password manager"
echo "2. Delete the credentials file: rm ./configs/production-credentials.txt"
echo "3. Apply database security: psql -f ./scripts/database-security.sql"
echo "4. Configure Scaleway Security Groups in console"
echo "5. Install fail2ban with custom configuration"
echo "6. Set up SSL certificate renewal automation"
echo "7. Test security monitoring alerts"
echo ""
echo -e "${RED}⚠️  SECURITY CHECKLIST:${NC}"
echo "☐ Change all default passwords"
echo "☐ Configure real SSL certificates (not self-signed)"
echo "☐ Update admin IP in security groups"
echo "☐ Enable database audit logging"
echo "☐ Configure fail2ban rules"
echo "☐ Set up security monitoring dashboard"
echo "☐ Test backup and restore procedures"
echo "☐ Configure intrusion detection system"