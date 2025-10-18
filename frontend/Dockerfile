# --------- Build stage ---------
FROM node:18-alpine AS build
WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY . .
# Vite reads VITE_* at build time; can be overridden by build args
ARG VITE_API_BASE_URL
ENV VITE_API_BASE_URL=${VITE_API_BASE_URL}
RUN npm run build

# --------- Runtime stage (Nginx) ---------
FROM nginx:1.25-alpine
WORKDIR /usr/share/nginx/html

COPY --from=build /app/dist ./

# Nginx with API reverse proxy to backend service name `backend`
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]


