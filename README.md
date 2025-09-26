<div align="center">
<img width="1200" height="475" alt="GHBanner" src="https://github.com/user-attachments/assets/0aa67016-6eaf-458a-adb2-6e31a0763ed6" />
</div>

# Run and deploy your AI Studio app

This contains everything you need to run your app locally.

View your app in AI Studio: https://ai.studio/apps/drive/1YvDF2_U_I6X2RFqOriTchUMgZ8vD3X7E

## Run Locally

**Prerequisites:**  Node.js


1. Install dependencies:
   `npm install`
2. Set the `GEMINI_API_KEY` in [.env.local](.env.local) to your Gemini API key
3. Run the app:
   `npm run dev`
Remove index.tsx from root (not from src)
Ensure Dockerfile is populated.
Ensure .dockerignore is populated

Dockerfile:

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




.dockerignore:

# Git and version control
.git
.gitignore

# Dependencies - these will be installed inside the container
node_modules
backend/node_modules

# Build output - this will be generated inside the container
dist
build

# IDE & Editor specific files
.vscode
.idea
*.suo
*.ntvs*
*.njsproj
*.sln
*.sw?

# Operating System specific files
.DS_Store
Thumbs.db

# Environment variables - should be configured in the deployment environment
.env
.env.*
