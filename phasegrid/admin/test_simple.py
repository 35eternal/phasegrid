from fastapi import FastAPI
import uvicorn

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Hello! PhaseGrid is working!"}

if __name__ == "__main__":
    print("Starting test server on http://localhost:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)