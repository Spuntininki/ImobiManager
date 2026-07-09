# =============================================================================
# ImobiManager Frontend - Dockerfile
# Multi-stage: dev (default) | build | prod
# =============================================================================

# ---- Dev stage ----
FROM node:22-alpine AS dev

WORKDIR /app

# Copy dependency manifests first for better caching
COPY package.json package-lock.json ./
RUN npm ci

COPY . .

EXPOSE 5173

ENV VITE_API_PROXY_TARGET=${VITE_API_PROXY_TARGET:-http://backend:8000}
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]

# ---- Build stage ----
FROM node:22-alpine AS build

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY . .

RUN npm run build

# ---- Prod stage (Nginx) ----
FROM nginx:alpine AS prod

COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]