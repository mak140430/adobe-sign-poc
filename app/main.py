from fastapi import FastAPI

app = FastAPI(title="Adobe Sign POC")

@app.get("/")
async def root():
    return {"message": "Adobe Sign API POC is kicking"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8081,
        ssl_keyfile="key.pem",
        ssl_certfile="cert.pem"
    )