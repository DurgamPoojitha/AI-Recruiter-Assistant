# Stage 1: Build the React application
FROM node:18-alpine AS builder

WORKDIR /app

# Copy package management files
COPY frontend-react/package*.json ./

# Install dependencies
RUN npm ci

# Copy the rest of the frontend source code
COPY frontend-react/ ./

# Build the application for production
RUN npm run build

# Stage 2: Serve the built application using Nginx
FROM nginx:alpine

# Copy the build output from the builder stage
COPY --from=builder /app/dist /usr/share/nginx/html

# Expose port 80
EXPOSE 80

# Start Nginx
CMD ["nginx", "-g", "daemon off;"]
