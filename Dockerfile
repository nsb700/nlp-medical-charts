FROM python:3.9

COPY . .

RUN apt-get update && apt-get install -y tesseract-ocr && apt-get install -y poppler-utils

RUN mkdir uploads && pip install --no-cache-dir --upgrade -r requirements.txt && pip install --upgrade pip && pip install Jinja2 --upgrade && pip install python-multipart && pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80"]
