# Build the React/Vite admin panel from the repo root.
FROM oven/bun:1 AS build
WORKDIR /app
ARG VITE_API_BASE=/api
ENV VITE_API_BASE=$VITE_API_BASE

# Copy manifest first for caching
COPY package.json bun.lockb* ./
RUN bun install --frozen-lockfile || bun install

# Copy the rest of the frontend source
COPY index.html ./
COPY tsconfig*.json ./
COPY vite.config.ts ./
COPY tailwind.config.ts ./
COPY postcss.config.js ./
COPY components.json ./
COPY public ./public
COPY src ./src

RUN bun run build

# Serve
FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY admin-panel.nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
