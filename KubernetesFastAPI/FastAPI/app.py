from fastapi import FastAPI

app = FastAPI()

items = []

@app.post("/items/")
async def create_item(item: dict):
    items.append(item)
    return {"item": item}

@app.get("/items/")
async def read_items():
    return {"items": items}
