import azure.functions as func
import pdfplumber
import logging
import json
import base64
import io
from pdf_parser_type1 import Type1PdfParser

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

@app.route(route="HttpExample")
def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')

    try:
        # Parse the JSON request body
        req_body = req.get_json()
    except ValueError:
        return func.HttpResponse(
            "Invalid JSON format",
            status_code=400
        )

    # Retrieve the base64 encoded PDF data
    base64_pdf = req_body.get('pdf_file')

    if not base64_pdf:
        return func.HttpResponse(
            "No base64 encoded data found in 'pdf_file'",
            status_code=400
        )

    try:
        # Decode the base64 PDF data
        pdf_data = base64.b64decode(base64_pdf)
    except base64.binascii.Error:
        return func.HttpResponse(
            "Invalid base64 encoded data",
            status_code=400
        )

    # Convert the decoded data to a BytesIO stream
    input_stream = io.BytesIO(pdf_data)
    output_data = "text here"
    try:
        output_data = parse_pdf_via_plumber(input_stream, pdf_data)

    except Exception as e:
        print(f"An error occurred while reading the PDF: {e}")
        return func.HttpResponse(
            "Error during PDF parsing",
            status_code=400
        )

    # Convert the data to JSON format
    json_data = json.dumps(output_data)

    return func.HttpResponse(
        json_data,
        mimetype="application/json",
        status_code=200
    )

def parse_pdf_via_plumber_and_use_words(input_stream, pdf_data_base64):

    text = ""
    input_stream = io.BytesIO(pdf_data_base64)
    with pdfplumber.open(input_stream) as pdf:
        for page_number, page in enumerate(pdf.pages):
            words = page.extract_words(use_text_flow=True)
            cleaned_text = " ".join([word['text'] for word in words])
            #print(cleaned_text)
            text += cleaned_text

    return text

def parse_pdf_via_plumber(input_stream, pdf_data_base64):
    text = ""

    with pdfplumber.open(input_stream) as pdf:
        # Iterate through the pages and extract text
        for page_number, page in enumerate(pdf.pages):
            text += page.extract_text()
    # print(text)

    pdf_parser = Type1PdfParser()

    word_text = parse_pdf_via_plumber_and_use_words(input_stream, pdf_data_base64)
    output_data = pdf_parser.parse_invoice_data(text,  word_text)
    return output_data


