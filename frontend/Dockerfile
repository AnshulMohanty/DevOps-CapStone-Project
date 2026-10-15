# ---- stage 1: build the static bundle ----
FROM node:22-alpine AS build
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY . .
RUN npm run build

# ---- stage 2: serve it with a non-root nginx ----
# nginx-unprivileged runs as uid 101 and listens on 8080 (a non-root user cannot bind port 80).
# Only dist/ is copied over: node, npm and the source never reach the final image.
FROM nginxinc/nginx-unprivileged:1.30-alpine
LABEL org.opencontainers.image.title="foundit-frontend" \
      org.opencontainers.image.description="FoundIt campus lost & found UI (React + nginx)"
ENV BACKEND_URL=http://backend:8000
COPY --from=build /app/dist /usr/share/nginx/html
COPY default.conf.template /etc/nginx/templates/default.conf.template
# The base image already runs as uid 101; stating it makes the non-root intent explicit and checkable.
USER 101
EXPOSE 8080
