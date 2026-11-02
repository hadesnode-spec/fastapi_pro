from fastapi import FastAPI

from app.routers import auth, products

app = FastAPI(title="Product API")
app.include_router(auth.router)
app.include_router(products.router)


@app.get("/")
def greet():
    return "Welcome"