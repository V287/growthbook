#!/bin/bash

echo "🚀 Starting GrowthBook Exposure API..."

# Run the FastAPI application
exec uvicorn exposure_api:app --host 0.0.0.0 --port 8000