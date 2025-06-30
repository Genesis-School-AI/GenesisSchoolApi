from typing import Union
from pydantic import BaseModel
from func import gen_response, qeury_database  # Ensure func.py is in the same directory or adjust the import path accordingly


# run with
# fastapi dev main.py
# or
# uvicorn toth_api:app --host 127.0.0.1 --port 8690 --reload

from fastapi import FastAPI

app = FastAPI()


class SetDataRequest(BaseModel):
    prompt: Union[str, None] = None
    k: Union[int, None] = 5  # Default value for k is set to 5


@app.get("/")
def read_root():
    return {"Hello": "adawdawdawdwa"}


@app.post("/fetch-response")
def set_data(request: SetDataRequest):
    return {
        "message": qeury_database(request.prompt, request.k),
        "k": request.k,
        "data": gen_response(request.prompt, request.k) if request.prompt else "No prompt provided"
    }
