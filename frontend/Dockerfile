FROM node:20-alpine AS build

WORKDIR /app
ARG VITE_API_BASE_URL=/api
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL
ENV NODE_OPTIONS=--max-old-space-size=2048

COPY package.json tsconfig.json tsconfig.app.json vite.config.ts tailwind.config.js postcss.config.js index.html ./
COPY src ./src
RUN npm install --silent
RUN npx tsc --noEmit
RUN npm run build

FROM nginx:1.27-alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html
