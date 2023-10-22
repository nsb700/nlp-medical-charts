from fastapi import FastAPI, UploadFile
from models import Label, Chart
from pathlib import Path
from fastapi.middleware.cors import CORSMiddleware
import os
from transformers import pipeline
from fastapi.templating import Jinja2Templates
from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi import BackgroundTasks


app = FastAPI()

origins = [
    "*",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = Path() / "uploads"
templates = Jinja2Templates(Path() / "templates")
labels = {}
app.mount(
    "/static",
    StaticFiles(directory=Path() / "static"),
    name="static"
)

# Initialize the zero-shot classification pipeline
classifier = pipeline('zero-shot-classification', model='facebook/bart-large-mnli')

@app.get("/")
async def root(request: Request):
    return  templates.TemplateResponse("zeroshot.html", context={"request": request})


# Get all labels
@app.get("/labels/")
async def get_labels():
    return {"labels":labels}


# Get single label
@app.get("/labels/{label_id}/")
async def get_label(label_id: str):
    if label_id in labels.keys():
        return {"label text":labels[label_id]}            
    return {"message":f"Label id {label_id} not found"}


# Create single label
@app.post("/labels/")
async def create_label(label: Label):
    if label.id in labels.keys():
        return {"message":f"Label {label.text} already present."}
    else:
        labels[label.id] = label.text
        return {"message":f"Label {label.text} added"}


# Delete single label
@app.delete("/labels/{label_id}/")
async def delete_label(label_id: str):
    if label_id in labels.keys():
        del labels[label_id]
        return {"message":f"Label id {label_id} deleted."} 
    else:
        return {"message":f"Label id {label_id} not found to delete."}


@app.post("/uploadfile/")
async def upload_file(file_to_upload: UploadFile):
    path_of_uploaded_file = get_path_of_uploaded_file()
    if path_of_uploaded_file:
        return {"message": "Only one file allowed to be uploaded"}
    data = await file_to_upload.read()
    save_to = UPLOAD_DIR / file_to_upload.filename
    with open(save_to, 'wb') as f:
        f.write(data)
    return {"message": f"File {os.path.basename(file_to_upload.filename)} uploaded"}


def get_path_of_uploaded_file():
    list_of_files = os.listdir(UPLOAD_DIR)
    if len(list_of_files) == 1:
        path_of_uploaded_file = os.path.join(UPLOAD_DIR, list_of_files[0])
        return path_of_uploaded_file
    else:
        return None


@app.post("/zeroshot/", response_class=HTMLResponse)
async def run_zeroshot_classification(request: Request):
    path_of_uploaded_file = get_path_of_uploaded_file()
    if path_of_uploaded_file:
        chart = Chart(path_of_uploaded_file)
        chart.read_text_from_chart()
        all_text = ' '.join(chart.list_of_text)
        user_input_labels = [v for k,v in labels.items()]
        zero_shot_result = classifier(all_text, candidate_labels=user_input_labels)
        label_scores = dict(zip(zero_shot_result['labels'], zero_shot_result['scores']))
        sequence = zero_shot_result['sequence']
        labels.clear
        await delete_file()
        return templates.TemplateResponse("zeroshot_result.html",
                                          context={
                                            "request":request,
                                            "label_scores":label_scores,
                                            "sequence":sequence
                                          }
                                        )
    else:
        return {"message": "No file uploaded"}


@app.post("/deletefile/")
async def delete_file():
    path_of_uploaded_file = get_path_of_uploaded_file()
    if path_of_uploaded_file:
        os.remove(path_of_uploaded_file)
        return {"message": f"File {os.path.basename(path_of_uploaded_file)} deleted"}
    else:
        return {"message": "No file uploaded"}