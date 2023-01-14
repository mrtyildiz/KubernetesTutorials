from fastapi import FastAPI
from uvicorn import run

app = FastAPI()

items = []

@app.post("/items/")
async def create_item(item: dict):
    items.append(item)
    return {"item": item}

@app.get("/items/")
async def read_items():
    return {"items": items}

if __name__ == "__main__":
    run(app, host="0.0.0.0", port=8000)
