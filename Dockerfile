FROM python:3.11-slim

WORKDIR /app

# Copy project files
COPY . .

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install --no-cache-dir -r pyproject.toml

# Create .streamlit directory and config
RUN mkdir -p .streamlit
COPY .streamlit/config.toml .streamlit/config.toml

# Expose ports
EXPOSE 5000 8000

# Start both services
CMD ["sh", "-c", "cd backend && python main.py & streamlit run app.py --server.port 5000 --server.address 0.0.0.0"]