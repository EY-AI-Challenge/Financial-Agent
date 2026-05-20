# Multi-stage Dockerfile for Financial Frontend

# Development & Build stage
FROM node:20-alpine AS dev

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci

# Copy source code
COPY . .

# Expose dev server port
EXPOSE 3000

# Default command runs dev server (can be overridden for build)
CMD ["npm", "run", "dev"]

# Production build stage
FROM node:20-alpine AS builder

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

# Production stage - lightweight image
FROM node:20-alpine AS prod

WORKDIR /app

# Install serve for static file serving
RUN npm install -g serve

# Copy built files from builder
COPY --from=builder /app/dist ./dist

EXPOSE 3000

# Serve the built app
CMD ["serve", "-s", "dist", "-l", "3000"]
