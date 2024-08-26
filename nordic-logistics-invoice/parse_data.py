import os
from functiona_app import *
def start():
    input_dir = './input_pdf'
    output_dir = './output'

    for filename in os.listdir(input_dir):
        if filename.endswith('.pdf'):
            pdf_path = os.path.join(input_dir, filename)

            # Read the content of the PDF file and convert to a base64 string
            with open(pdf_path, 'rb') as pdf_file:
                pdf_data = pdf_file.read()
                base64_string = base64.b64encode(pdf_data).decode('utf-8')

            input_stream = io.BytesIO(pdf_data)
            # Parse the invoice data
            data = parse_pdf_via_plumber(input_stream, base64.b64decode(base64_string))

            # Define the output JSON file name
            json_filename = os.path.splitext(filename)[0] + '.json'

            # Write the output JSON to a file in the output directory
            with open(os.path.join(output_dir, json_filename), 'w') as json_file:
                json.dump(data, json_file, indent=2)

            print(f'Parsed {filename} and saved to {json_filename}')


if __name__ == "__main__":
    start()