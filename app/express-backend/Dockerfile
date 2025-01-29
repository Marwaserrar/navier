FROM node:16

WORKDIR /app

COPY package.json package-lock.json ./

RUN npm install

COPY . .

# Ensure the /tmp directory exists
RUN mkdir -p /tmp

# Expose the port
EXPOSE 5000

CMD ["node", "index.js"]