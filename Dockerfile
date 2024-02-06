FROM python:3.8.18-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
VOLUME ["./trending"]
CMD ["python", "main.py"]