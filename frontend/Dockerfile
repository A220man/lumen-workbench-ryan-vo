FROM node:24-alpine AS builder

WORKDIR /app

# Copy package and lock files
COPY frontend/package.json frontend/package-lock.json* ./
COPY frontend/tsconfig.json ./
COPY frontend/vite.config.ts ./
COPY frontend/index.html ./

# Install all dependencies (build requires devDependencies like vite and tsc)
RUN npm ci

# Copy source code
COPY frontend/src/ ./src/

# Build the application
RUN npm run build

# Production stage
FROM nginx:alpine AS production

# Copy static files from builder
COPY --from=builder /app/dist/ /usr/share/nginx/html/

EXPOSE 80

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD wget -q --silent --fail http://localhost:80/ || exit 1

CMD ["nginx", "-g", "daemon off;"]