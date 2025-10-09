# Frontend Dockerfile for RAG Platform

FROM node:20-slim

# Set working directory
WORKDIR /app/frontend

# Install yarn
RUN npm install -g yarn

# Copy package files
COPY package.json yarn.lock ./

# Install dependencies
RUN yarn install --frozen-lockfile

# Copy application code
COPY . .

# Expose port
EXPOSE 3000

# Start the development server
CMD ["yarn", "start"]
