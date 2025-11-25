import uvicorn

if __name__ == "__main__":
    uvicorn.run("main:app", port=8000, log_level="info", ssl_keyfile="./key.pem", ssl_certfile="./cert.pem")
