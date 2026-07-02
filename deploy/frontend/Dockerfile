FROM node:22-alpine

WORKDIR /app

COPY frontend/package*.json ./  

COPY frontend/package-lock.json ./

# RUN npm ci || npm install

RUN npm install -g npm@11.5.2 && npm install -D @vitejs/plugin-react 

COPY frontend/ ./

EXPOSE 3000

CMD ["npm", "run", "start"]
