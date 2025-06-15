FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy toàn bộ thư mục app vào container
COPY app/ ./app/

CMD ["python", "app/report.py"]