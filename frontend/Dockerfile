# Frontend Dockerfile - Production optimized for Scaleway
FROM node:20-alpine as builder

WORKDIR /app

# Copy package files
COPY package*.json ./
RUN npm ci --only=production

# Copy source and build
COPY . .
RUN npm run build

# Production stage - Nginx
FROM nginx:alpine

# Create the web directory
RUN mkdir -p /var/www/piazzati

# Copy build output to the correct directory
COPY --from=builder /app/dist /var/www/piazzati

# Copy nginx configuration 
COPY nginx/nginx.prod.conf /etc/nginx/conf.d/default.conf

# Create health endpoint
RUN echo '<!DOCTYPE html><html><body>OK</body></html>' > /var/www/piazzati/health

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD wget --no-verbose --tries=1 --spider http://localhost/health || exit 1

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]