# Stage 1: Build the frontend assets
# Use a Node.js image that includes build tools
FROM node:18-alpine AS builder

# Set the working directory
WORKDIR /app

# Copy all package files and install dependencies for the frontend
COPY package*.json ./
COPY tsconfig*.json ./
COPY vite.config.ts ./
RUN npm install

# Copy the rest of the frontend source code
COPY . .

# Build the frontend application
RUN npm run build

# Stage 2: Build the production server
# Use a lightweight Node.js image for the final container
FROM node:18-alpine

WORKDIR /app

# Copy the built frontend assets from the 'builder' stage
COPY --from=builder /app/dist ./dist

# Copy the backend's package files
COPY backend/package*.json ./backend/

# Install only production dependencies for the backend
RUN npm install --prefix backend --omit=dev

# Copy the backend server code
COPY backend/server.js ./backend/

# Expose the port the app runs on (Cloud Run will automatically use this)
EXPOSE 8080

# The command to run the application
CMD [ "npm", "start", "--prefix", "backend" ]
