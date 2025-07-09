from typing import Union
from pydantic import BaseModel
from typing import Dict, Any
# Ensure func.py is in the same directory or adjust the import path accordingly
from func import gen_response, qeury_database, add_document , gen_gemini


# run with
# uvicorn toth_api:app --host 127.0.0.1 --port 8690 --reload

#subject list
# bio,phy,chem,math,eng,geo,his,eco,pol,soc,art,music,pe,comsci

from fastapi import FastAPI

app = FastAPI()


class SetDataRequest(BaseModel):
    prompt: Union[str, None] = None
    k: Union[int, None] = 5  # Default value for k is set to 5
    room_id: Union[int, None] = None  # Optional room_id field
    year_id: Union[int, None] = None  # Optional year_id field
    subject_id: Union[str, None] = None  # Optional subject_id field
    
class SetDataGemini(BaseModel):
    prompt: Union[str, None] = None
    k: Union[int, None] = 5  # Default value for k is set to 5
    room_id: Union[int, None] = None  # Optional room_id field
    year_id: Union[int, None] = None  # Optional year_id field
    subject_id: Union[str, None] = None  # Optional subject_id field
    
class AddDocumentRequest(BaseModel):
    content: Dict[str, Any] 


@app.get("/")
def read_root():
    return {"Hello user": "toth is running pls use /fetch-response or /add-document"}


@app.post("/fetch-response")
def set_data(request: SetDataRequest):
    return {
       #  "message": qeury_database(request.prompt, request.k, request.room_id, request.year_id, request.subject_id),
        "k": request.k,
        "data": gen_response(request.prompt, request.k, request.room_id, request.year_id, request.subject_id) if request.prompt else "No prompt provided"
    }
    
@app.post("/fetch-gemini")
def set_data(request: SetDataGemini):
    return {
       #  "message": qeury_database(request.prompt, request.k, request.room_id, request.year_id, request.subject_id),
        "k": request.k,
        "data": gen_gemini(request.prompt, request.k, request.room_id, request.year_id, request.subject_id) if request.prompt else "No prompt provided"
    }
    
@app.post("/add-document")
def set_data(request: AddDocumentRequest):
    return {
        "message": request.content,
        "content": add_document(request.content)
    }
