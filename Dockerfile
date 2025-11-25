FROM python:3.13

EXPOSE 8000
WORKDIR /app
COPY . /app
RUN apt update -y && \
    apt install -y --no-install-recommends git libgdal-dev && \
    rm -rf /var/lib/apt/lists/*

RUN python -m pip install -r requirements.txt
ENV API_KEY="dev-demo-key-change-me"

CMD ["uvicorn", "main:app", "--port=8000", "--ssl-keyfile=./key.pem", "--ssl-certfile=./cert.pem"]