from pydantic import BaseModel
from PyPDF2 import PdfReader, PdfWriter
from pdf2image import convert_from_path
import pytesseract
import os


class Label(BaseModel):
    id: str
    text: str


class Chart:
    def __init__(self, path):
        self.file_path: str = path
        self.file_dir_path: str = os.path.dirname(path)
        self.list_of_text: list = []
        self.app_params_dict = {}

    def is_page_scanned(self, page_text):
        if len(page_text) <= 2:
            return True
        else:
            return False

    def get_scanned_text_from(self, page):
        output = PdfWriter()
        output.add_page(page)
        temp_file_path = os.path.join(self.file_dir_path, 'temp')
        output_stream = open(temp_file_path, 'wb')
        output.write(output_stream)
        output_stream.close()
        image = convert_from_path(temp_file_path)
        text = pytesseract.image_to_string(image[0])
        os.remove(temp_file_path)
        return text

    def read_app_params(self):
        f = open('app_params', 'r')
        for line in f.readlines():
            vals = line.split('=')
            self.app_params_dict[vals[0]] = vals[1]


    def read_text_from_chart(self):
        self.read_app_params()
        pytesseract.pytesseract.tesseract_cmd = self.app_params_dict['tesseract_binary_path']
        reader = PdfReader(self.file_path)
        for page in reader.pages:
            page_text = page.extract_text()
            if self.is_page_scanned(page_text):
                page_text = self.get_scanned_text_from(page)
            self.list_of_text.append(page_text)
