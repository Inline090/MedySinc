FROM node:22-slim AS build

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY . .

# NEXT_PUBLIC_ variables must be present at BUILD time, because Next.js writes them
# straight into the compiled client JavaScript. Setting them at runtime does nothing.
ARG NEXT_PUBLIC_API_URL
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL
RUN npm run build

FROM node:22-slim AS run

WORKDIR /app
ENV NODE_ENV=production

# The standalone output is a self-contained server with only the files it needs,
# which is why next.config.mjs sets output: "standalone".
COPY --from=build /app/.next/standalone ./
COPY --from=build /app/.next/static ./.next/static

EXPOSE 3000
CMD ["node", "server.js"]
