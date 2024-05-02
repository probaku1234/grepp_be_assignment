from fastapi import FastAPI

from database import engine
import models
from db_uploader import init_data
from routers.user_router import user_router
from routers.exam_router import exam_router
import uvicorn

# TODO: db no volume
# TODO: insert data when start
models.Base.metadata.create_all(bind=engine)

init_data()

app = FastAPI()

app.include_router(user_router)
app.include_router(exam_router)


@app.get("/")
def read_root():
    return {"Hello": "World"}


if __name__ == '__main__':
    uvicorn.run("main:app")