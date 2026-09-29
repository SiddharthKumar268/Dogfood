FROM python:3.12-slim
WORKDIR /app
COPY backend ./backend
COPY fixtures.json ./fixtures.json
WORKDIR /app/backend
RUN pip install --no-cache-dir -r requirements.txt
EXPOSE 8080
CMD ["python", "avi.py"]
