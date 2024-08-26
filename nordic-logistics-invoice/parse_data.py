import os
from functiona_app import *

INPUT_DIR = './input_pdf'
OUTPUT_DIR = './output'


def process_file(pdf_path, filename):
    with open(pdf_path, 'rb') as pdf_file:
        pdf_data = pdf_file.read()
        base64_string = base64.b64encode(pdf_data).decode('utf-8')

    input_stream = io.BytesIO(pdf_data)
    # Parse the invoice data
    data = parse_pdf_via_plumber(input_stream, base64.b64decode(base64_string))

    # Define the output JSON file name
    json_filename = os.path.splitext(filename)[0] + '.json'

    # Write the output JSON to a file in the output directory
    with open(os.path.join(OUTPUT_DIR, json_filename), 'w') as json_file:
        json.dump(data, json_file, indent=2)

    print(f'Parsed {filename} and saved to {json_filename}')

def start(file_name=""):
    if file_name == "":
        for filename in os.listdir(INPUT_DIR):
            if filename.endswith('.pdf'):
                pdf_path = os.path.join(INPUT_DIR, filename)
                process_file(pdf_path, filename)
    else:
        pdf_path = os.path.join(INPUT_DIR, file_name)
        process_file(pdf_path, file_name)



if __name__ == "__main__":
    start()