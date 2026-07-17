FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN pip install --no-cache-dir .
ENV CASE_DATA_DIR=/app/data
EXPOSE 8000
CMD ["uvicorn", "case_manager.api:app", "--host", "0.0.0.0", "--port", "8000"]
