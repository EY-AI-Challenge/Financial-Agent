from fastapi import FastAPI

app = FastAPI(title="Financial Decision Support API")

@app.get("/")
def read_root():
    return {"message": "Welcome to the Financial Decision Support API"}
