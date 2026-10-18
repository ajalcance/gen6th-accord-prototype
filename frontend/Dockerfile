# Next.js production image (multi-stage, non-root).
FROM node:22-alpine@sha256:16e22a550f3863206a3f701448c45f7912c6896a62de43add43bb9c86130c3e2 AS build
WORKDIR /app
# The API rewrite in next.config.ts is read when `next build` evaluates the config, so the
# origin must be present at BUILD time; the run stage repeats it so build and runtime agree.
# Empty (the default) keeps the frontend-only shape: no /api rewrite, connection disabled.
ARG ACCORD_API_ORIGIN=""
ARG ACCORD_CONNECTION_ENABLED="false"
ENV ACCORD_API_ORIGIN=$ACCORD_API_ORIGIN \
    ACCORD_CONNECTION_ENABLED=$ACCORD_CONNECTION_ENABLED
COPY package.json package-lock.json ./
COPY vendor/braces/braces-3.0.4-accord.1.tgz ./vendor/braces/
RUN npm ci
COPY . .
RUN npm run build

FROM node:22-alpine@sha256:16e22a550f3863206a3f701448c45f7912c6896a62de43add43bb9c86130c3e2 AS run
WORKDIR /app
ARG ACCORD_API_ORIGIN=""
ARG ACCORD_CONNECTION_ENABLED="false"
ENV NODE_ENV=production \
    ACCORD_API_ORIGIN=$ACCORD_API_ORIGIN \
    ACCORD_CONNECTION_ENABLED=$ACCORD_CONNECTION_ENABLED
COPY --from=build /app ./
# Numeric uid/gid so the runtime can verify non-root without resolving a name (hadolint DL3066).
RUN addgroup -S -g 10001 app && adduser -S -u 10001 -G app app
USER 10001
EXPOSE 3000
CMD ["npm", "run", "start"]
