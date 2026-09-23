from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def home():
    return {"message": "hello"}

@app.get("/foods")
def get_foods():
    return [
        {"id": 1, "name": "Jollof rice"},
        {"id": 2, "name": "Eba"},
        {"id": 3, "name": "Egusi"} 
    ]