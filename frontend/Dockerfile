# Frontend Next.js server on Cloud Run.
# Build from repository root:
#   docker build -f frontend/Dockerfile .
# Env vars are injected by Cloud Run at runtime — NOT baked at build time (no NEXT_PUBLIC_* in Docker build args).
# Set NEXT_PUBLIC_API_URL, NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY, etc. as Cloud Run env vars (deploy-frontend step).

FROM --platform=linux/amd64 node:20-slim AS builder
WORKDIR /frontend

COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci

COPY frontend/ ./

# Clerk publishable key is required during `next build` for prerender.
# This value is public by design (NEXT_PUBLIC_), passed from CI as a build arg.
ARG NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=""
ENV NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=${NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY}

# Build Next.js app (server mode — no output: export)
RUN npm run build

# Production image
FROM --platform=linux/amd64 node:20-slim AS runner
WORKDIR /frontend

ENV NODE_ENV=production
ENV PORT=8080
ENV HOSTNAME=0.0.0.0

COPY --from=builder /frontend/public ./public
COPY --from=builder /frontend/.next/standalone ./
COPY --from=builder /frontend/.next/static ./.next/static

EXPOSE 8080
CMD ["node", "server.js"]
