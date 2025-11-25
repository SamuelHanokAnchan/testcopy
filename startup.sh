export API_KEY=dev-demo-key-change-me
python -m uvicorn main:app --port=8000 --ssl-keyfile="key.pem" --ssl-certfile="cert.pem"