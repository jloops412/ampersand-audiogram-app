# Stage 1: Build the React frontend
# Use an official Node.js image. Alpine is a small, secure Linux distribution.
FROM node:18-alpine AS builder
# Set the working directory inside the container
WORKDIR /app
# Copy package.json and package-lock.json to leverage Docker's layer caching
COPY package*.json ./
# Install frontend dependencies
RUN npm install
# Copy the rest of your app's source code
COPY . .
# Build the frontend for production
RUN npm run build

# Stage 2: Install backend dependencies
# Use a fresh stage to keep the final image small
FROM node:18-alpine AS backend-builder
WORKDIR /app
# Copy only the backend's package files
COPY backend/package*.json ./backend/
# Install only production dependencies for the backend
RUN cd backend && npm install --production
# Copy the backend server code
COPY backend/server.js ./backend/

# Stage 3: Create the final production image
FROM node:18-alpine
# Set the working directory
WORKDIR /app

# Copy the built frontend assets from the 'builder' stage
COPY --from=builder /app/dist ./dist

# Copy the backend server and its installed dependencies from the 'backend-builder' stage
COPY --from=backend-builder /app/backend ./backend

# The port your backend server listens on
EXPOSE 8080

# The command to start your backend server
CMD ["node", "backend/server.js"]
