# Stage 1: Build the React frontend
FROM node:18-alpine AS frontend-builder
LABEL name="ASR-TTS-Curator"
LABEL version="0.1"
LABEL description='''The voice and text data annotation platform. \
                    Enables the annotation of text to speech targets for TTS; \
                    speech to text targets for ASR applications.'''

ARG APP_PORT
ARG VITE_BACKEND_URL
ENV APP_PORT=${APP_PORT}
ENV VITE_BACKEND_URL=${VITE_BACKEND_URL}

WORKDIR /app

# Copy package files and install dependencies
COPY frontend/package.json ./frontend/
RUN cd frontend && npm install && npm i --save-dev @types/node

# Copy the rest of the frontend code
COPY frontend/ ./frontend/

# Build the frontend application
RUN cd frontend && npm run build

# Stage 2: Build the Python backend and create the final image
FROM python:3.11-slim
COPY --from=public.ecr.aws/awsguru/aws-lambda-adapter:0.9.1 /lambda-adapter /opt/extensions/lambda-adapter

WORKDIR /app/backend

# Install system dependencies needed for pymysql and other libraries
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    curl \
    ffmpeg \
    default-libmysqlclient-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend application code
COPY backend/ .

# Copy built frontend from the builder stage into a 'static' directory in the backend
COPY --from=frontend-builder /app/frontend/dist ./static

# Create the recordings directory
RUN mkdir -p /app/backend/data/recordings && chmod -R 777 /app/backend/data

# Expose the port the backend will run on
EXPOSE ${APP_PORT}

# Start Uvicorn server
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port $APP_PORT"]