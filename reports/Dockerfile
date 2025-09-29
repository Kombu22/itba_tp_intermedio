FROM python:3.11-slim
WORKDIR /app

COPY reports/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY reports/report.py .

CMD ["python", "report.py"]
