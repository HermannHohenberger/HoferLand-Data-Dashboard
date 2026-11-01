# Node 22 LTS, passend zur lokalen Entwicklung. Node 20 ist seit April 2026 ohne Updates.
FROM node:22-alpine AS build

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

# Stabiler Zweig. 1.27 ist eine beendete Mainline.
FROM nginx:1.31-alpine

COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
