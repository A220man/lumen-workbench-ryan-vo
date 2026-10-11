FROM node:24-alpine AS builder

WORKDIR /app

# Copy package files first for better caching
COPY frontend/package.json* ./
COPY frontend/tsconfig.json* ./
COPY frontend/vite.config.ts* ./

# Install dependencies
RUN npm ci --only=production

# Copy source code
COPY frontend/src/ ./frontend/src/

# Build the application
RUN npm run build

# Production stage
FROM nginx:alpine AS production

# Copy static files from builder
COPY --from=builder /app/frontend/dist/ /usr/share/nginx/html/

EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD wget -q --silent --fail http://localhost:3000/health || exit 1

CMD ["nginx", "-g", "listen 80; daemon on;"]