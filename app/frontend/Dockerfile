# Stage 1: Build the React app
FROM node:18 as build

WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

# Stage 2: Serve using Nginx with proper configuration
FROM nginx:alpine

# Remove ALL default configurations and entrypoint scripts
RUN rm -rf /etc/nginx/conf.d/* && \
    rm -rf /docker-entrypoint.d/*

# Copy built assets and custom config
COPY --from=build /app/build /usr/share/nginx/html
COPY nginx.conf /etc/nginx/nginx.conf

# Verify configuration during build
RUN nginx -t

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
