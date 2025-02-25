FROM python:3.11-slim

WORKDIR /app

# Copy requirements first to leverage Docker cache
COPY src/requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY src/ /app/

ENTRYPOINT ["python", "main.py"]