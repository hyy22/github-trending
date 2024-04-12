FROM python:3.8.18-slim
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
EXPOSE 80
VOLUME ["/app/dist"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "80"]