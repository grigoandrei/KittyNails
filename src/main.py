from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()
items_db = {}

class Item(BaseModel):
    name: str
    price: float
    is_offer: bool | None = None

@app.get("/")
def read_root():
    return {"Hello" : "World"}

@app.get("/items/{item_id}")
def read_item(item_id: int, q: str | None = None):
    if item_id not in items_db:
        return {"error": "Item not found"}
    item = items_db[item_id]
    return {"item_id": item_id, "item": item}

@app.put("/items/{item_id}")
def update_item(item_id: int, item: Item):
    items_db[item_id] = item
    return {"item_name" : item.name, "item_id": item_id}