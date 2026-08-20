# Step 1: Build stage
FROM node:20-alpine AS build

WORKDIR /app
COPY package*.json ./
RUN npm install

COPY . .
RUN npm run build

# Step 2: Serve stage
FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html

# Custom nginx config with reverse proxy to FastAPI backend
RUN echo 'server { \
    listen 80; \
    location /v1/ { \
        proxy_pass http://backend:8000/v1/; \
        proxy_set_header Host $host; \
        proxy_set_header X-Real-IP $remote_addr; \
    } \
    location / { \
        root /usr/share/nginx/html; \
        index index.html index.htm; \
        try_files $uri $uri/ /index.html; \
    } \
}' > /etc/nginx/conf.d/default.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
