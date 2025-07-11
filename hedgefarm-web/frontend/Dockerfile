# build stage
FROM node:20-alpine AS build
WORKDIR /app
COPY . .
RUN npm ci && npm run build

# serve stage
FROM nginx:1.25-alpine
COPY --from=build /app/dist /usr/share/nginx/html