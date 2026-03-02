FROM python:3.11-slim


ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY servidor/ /app/servidor/
COPY cliente/ /app/cliente/

EXPOSE 5000

CMD ["python3", "servidor/proxy_server.py", "--family", "dual", "--host", "::", "--port", "5000"]