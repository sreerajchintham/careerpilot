from fastapi import FastAPI

app = FastAPI(title="CareerPilot Agent API")


@app.get("/health")
def health_check():
    return {"status": "ok"}


