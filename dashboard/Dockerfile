FROM python:3.13-alpine

WORKDIR /app

COPY server.py .
COPY static ./static

EXPOSE 80

CMD ["python", "server.py"]
