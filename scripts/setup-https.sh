#!/bin/bash

# =============================================================================
# SCALEWAY HTTPS & LOAD BALANCER SETUP SCRIPT
# =============================================================================
# Setup automatico SSL/TLS certificate e Load Balancer configuration
# Usage: ./scripts/setup-https.sh
# =============================================================================

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
DOMAIN="piazzati.yourdomain.com"
API_SUBDOMAIN="api.piazzati.yourdomain.com"
GRAFANA_SUBDOMAIN="grafana.piazzati.yourdomain.com"
SCALEWAY_REGION="fr-par"
SCALEWAY_ZONE="fr-par-1"

echo -e "${BLUE}==============================================================================${NC}"
echo -e "${BLUE}PIAZZATI - SCALEWAY HTTPS & LOAD BALANCER SETUP${NC}"
echo -e "${BLUE}==============================================================================${NC}"

# Check prerequisites
echo -e "${YELLOW}[1/8] Checking prerequisites...${NC}"

if ! command -v scw &> /dev/null; then
    echo -e "${RED}Error: Scaleway CLI not found. Install with:${NC}"
    echo "curl -o scw https://github.com/scaleway/scaleway-cli/releases/latest/download/scw-linux-x86_64"
    echo "chmod +x scw && sudo mv scw /usr/local/bin/"
    exit 1
fi

if ! command -v openssl &> /dev/null; then
    echo -e "${RED}Error: OpenSSL not found. Install openssl package.${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Prerequisites OK${NC}"

# Configure Scaleway CLI
echo -e "${YELLOW}[2/8] Configuring Scaleway CLI...${NC}"

if [ -z "$SCALEWAY_ACCESS_KEY" ] || [ -z "$SCALEWAY_SECRET_KEY" ] || [ -z "$SCALEWAY_PROJECT_ID" ]; then
    echo -e "${RED}Error: Missing Scaleway credentials. Set environment variables:${NC}"
    echo "export SCALEWAY_ACCESS_KEY=your_access_key"
    echo "export SCALEWAY_SECRET_KEY=your_secret_key"
    echo "export SCALEWAY_PROJECT_ID=your_project_id"
    exit 1
fi

scw config set access-key=$SCALEWAY_ACCESS_KEY
scw config set secret-key=$SCALEWAY_SECRET_KEY
scw config set default-project-id=$SCALEWAY_PROJECT_ID
scw config set default-zone=$SCALEWAY_ZONE

echo -e "${GREEN}✅ Scaleway CLI configured${NC}"

# Generate SSL certificate (self-signed for testing, replace with real cert)
echo -e "${YELLOW}[3/8] Generating SSL certificate...${NC}"

mkdir -p ./ssl
cd ./ssl

# Generate private key
openssl genrsa -out piazzati.key 4096

# Generate certificate signing request
openssl req -new -key piazzati.key -out piazzati.csr -subj "/C=IT/ST=Italy/L=Milan/O=PiazzaTi/CN=$DOMAIN"

# Generate self-signed certificate (90 days)
openssl x509 -req -days 90 -in piazzati.csr -signkey piazzati.key -out piazzati.crt

# Create certificate chain
cat piazzati.crt > piazzati-chain.crt

echo -e "${GREEN}✅ SSL certificate generated${NC}"
echo -e "${YELLOW}⚠️  For production, replace with real SSL certificate from Let's Encrypt or CA${NC}"

cd ..

# Upload SSL certificate to Scaleway
echo -e "${YELLOW}[4/8] Uploading SSL certificate to Scaleway...${NC}"

CERT_CONTENT=$(cat ./ssl/piazzati-chain.crt)
KEY_CONTENT=$(cat ./ssl/piazzati.key)

CERT_ID=$(scw lb certificate create \
    name="piazzati-ssl-cert" \
    certificate-chain="$CERT_CONTENT" \
    private-key="$KEY_CONTENT" \
    --output json | jq -r '.id')

if [ "$CERT_ID" = "null" ] || [ -z "$CERT_ID" ]; then
    echo -e "${RED}Error: Failed to upload SSL certificate${NC}"
    exit 1
fi

echo -e "${GREEN}✅ SSL certificate uploaded (ID: $CERT_ID)${NC}"

# Create Load Balancer
echo -e "${YELLOW}[5/8] Creating Load Balancer...${NC}"

LB_ID=$(scw lb lb create \
    name="piazzati-lb-prod" \
    type="LB-S" \
    --output json | jq -r '.id')

if [ "$LB_ID" = "null" ] || [ -z "$LB_ID" ]; then
    echo -e "${RED}Error: Failed to create Load Balancer${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Load Balancer created (ID: $LB_ID)${NC}"

# Wait for Load Balancer to be ready
echo -e "${YELLOW}[6/8] Waiting for Load Balancer to be ready...${NC}"
sleep 30

# Get Load Balancer IP
LB_IP=$(scw lb lb get $LB_ID --output json | jq -r '.ip[0].ip_address')
echo -e "${GREEN}✅ Load Balancer IP: $LB_IP${NC}"

# Create backend pools
echo -e "${YELLOW}[7/8] Creating backend pools...${NC}"

# Backend for API
API_BACKEND_ID=$(scw lb backend create \
    lb-id=$LB_ID \
    name="piazzati-backend-pool" \
    forward-protocol="http" \
    forward-port=8000 \
    forward-port-algorithm="roundrobin" \
    health-check-port=8000 \
    health-check-delay="10s" \
    health-check-timeout="5s" \
    health-check-max-retries=3 \
    health-check-http-uri="/health" \
    health-check-http-method="GET" \
    health-check-http-code=200 \
    --output json | jq -r '.id')

# Backend for Grafana
GRAFANA_BACKEND_ID=$(scw lb backend create \
    lb-id=$LB_ID \
    name="grafana-backend-pool" \
    forward-protocol="http" \
    forward-port=3000 \
    forward-port-algorithm="roundrobin" \
    sticky-sessions="cookie" \
    sticky-sessions-cookie-name="grafana_session" \
    health-check-port=3000 \
    health-check-delay="15s" \
    health-check-timeout="10s" \
    health-check-max-retries=3 \
    health-check-http-uri="/api/health" \
    health-check-http-method="GET" \
    health-check-http-code=200 \
    --output json | jq -r '.id')

echo -e "${GREEN}✅ Backend pools created${NC}"

# Create frontend rules
echo -e "${YELLOW}[8/8] Creating frontend rules...${NC}"

# HTTPS frontend for API
scw lb frontend create \
    lb-id=$LB_ID \
    name="piazzati-https-frontend" \
    inbound-port=443 \
    backend-id=$API_BACKEND_ID \
    timeout-client="30s" \
    certificate-id=$CERT_ID

# HTTP redirect frontend
scw lb frontend create \
    lb-id=$LB_ID \
    name="piazzati-http-redirect" \
    inbound-port=80 \
    backend-id=$API_BACKEND_ID \
    timeout-client="10s"

# HTTPS frontend for Grafana
scw lb frontend create \
    lb-id=$LB_ID \
    name="grafana-https-frontend" \
    inbound-port=3000 \
    backend-id=$GRAFANA_BACKEND_ID \
    timeout-client="60s" \
    certificate-id=$CERT_ID

echo -e "${GREEN}✅ Frontend rules created${NC}"

# Summary
echo -e "${BLUE}==============================================================================${NC}"
echo -e "${GREEN}🎉 HTTPS & Load Balancer setup completed successfully!${NC}"
echo -e "${BLUE}==============================================================================${NC}"
echo ""
echo -e "${YELLOW}CONFIGURATION SUMMARY:${NC}"
echo -e "Load Balancer ID: ${GREEN}$LB_ID${NC}"
echo -e "Load Balancer IP: ${GREEN}$LB_IP${NC}"
echo -e "SSL Certificate ID: ${GREEN}$CERT_ID${NC}"
echo ""
echo -e "${YELLOW}DNS CONFIGURATION REQUIRED:${NC}"
echo -e "Add these DNS A records to your domain:"
echo -e "  ${DOMAIN} → ${LB_IP}"
echo -e "  ${API_SUBDOMAIN} → ${LB_IP}"
echo -e "  ${GRAFANA_SUBDOMAIN} → ${LB_IP}"
echo ""
echo -e "${YELLOW}ENDPOINTS:${NC}"
echo -e "  Main site: ${GREEN}https://$DOMAIN${NC}"
echo -e "  API: ${GREEN}https://$API_SUBDOMAIN${NC}"
echo -e "  Grafana: ${GREEN}https://$GRAFANA_SUBDOMAIN:3000${NC}"
echo ""
echo -e "${YELLOW}NEXT STEPS:${NC}"
echo "1. Configure DNS records as shown above"
echo "2. Add container IPs to backend pools"
echo "3. Test SSL certificate and endpoints"
echo "4. Consider replacing self-signed cert with real certificate"

# Save configuration
cat > ./configs/scaleway-https-config.env << EOF
SCALEWAY_LB_ID=$LB_ID
SCALEWAY_LB_IP=$LB_IP
SCALEWAY_SSL_CERT_ID=$CERT_ID
SCALEWAY_API_BACKEND_ID=$API_BACKEND_ID
SCALEWAY_GRAFANA_BACKEND_ID=$GRAFANA_BACKEND_ID
EOF

echo -e "${GREEN}✅ Configuration saved to ./configs/scaleway-https-config.env${NC}"
echo -e "${BLUE}==============================================================================${NC}"