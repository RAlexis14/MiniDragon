FROM python:3.12-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1

# context = ../apps
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# backend code
COPY backend/ .

# bring frontend static
ARG FRONTEND_DIR=frontend
COPY ${FRONTEND_DIR}/ /app/static/

EXPOSE 5000
CMD ["python", "app.py"]
