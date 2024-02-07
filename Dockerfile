FROM python:3.8.18-slim
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt && \
    python -m http.server 80 -d ./dist
EXPOSE 80
VOLUME ["./dist"]
CMD ["python", "main.py"]