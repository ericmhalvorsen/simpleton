# frontend/Dockerfile
FROM node:18-alpine as builder

WORKDIR /app

# Install dependencies
COPY package.json package-lock.json* ./
RUN npm install

# Copy frontend source
COPY . .

# Build the app
RUN npm run build

# Production stage
FROM node:18-alpine

WORKDIR /app

# Copy built assets and production dependencies
COPY --from=builder /app/package*.json ./
COPY --from=builder /app/.svelte-kit ./.svelte-kit
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/build ./build
COPY --from=builder /app/static ./static

# Expose the port the app runs on
EXPOSE 3000

# Run the application with host binding
CMD ["npm", "run", "preview", "--", "--host", "0.0.0.0"]
