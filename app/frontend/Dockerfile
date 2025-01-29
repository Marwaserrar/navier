# Stage 1: Build React App
FROM node:18 as build

WORKDIR /app

# Copy package.json and package-lock.json
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy the rest of the application code
COPY . .

# Build the React app
RUN npm run build

FROM nginx:latest as prod

COPY --from=build /app/dist /usr/share/nginx/html
RUN rm -rf /etc/nginx/nginx.conf
COPY nginx.conf /etc/nginx/nginx.conf
RUN cat /etc/nginx/nginx.conf
RUN echo "copied properly"

EXPOSE 80/tcp

CMD ["/usr/sbin/nginx", "-g", "daemon off;"]
