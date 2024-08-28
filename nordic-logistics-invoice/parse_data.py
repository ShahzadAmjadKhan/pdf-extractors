import os
from function_app import *
import pandas as pd
import pypdfium2 as pdfium
from pdf_parser_type2 import Type2PdfParser


def process_file_via_pypdfium2(pdf_path):
    pdf = pdfium.PdfDocument(pdf_path)
    text = ""
    for page_number in range(len(pdf)):
        page = pdf.get_page(page_number)
        page_text = page.get_textpage()
        text += page_text.get_text_range()
        # print(text)
    return text

def process_file(pdf_path, filename, output_dir):
    with open(pdf_path, 'rb') as pdf_file:
        pdf_data = pdf_file.read()
        base64_string = base64.b64encode(pdf_data).decode('utf-8')

    input_stream = io.BytesIO(pdf_data)
    # Parse the invoice data
    # data = parse_pdf_via_plumber(input_stream, base64.b64decode(base64_string))
    text = process_file_via_pypdfium2(pdf_path)
    pdf_parser = Type2PdfParser()
    data = pdf_parser.parse_invoice_data(text)

    # Define the output JSON file name
    json_filename = os.path.splitext(filename)[0] + '.json'

    # Write the output JSON to a file in the output directory
    with open(os.path.join(output_dir, json_filename), 'w') as json_file:
        json.dump(data, json_file, indent=2)

    print(f'Parsed {filename} and saved to {json_filename}')


def make_excel_file():
# Directory containing the JSON files
    input_dir = './output'
    output_file = './output/all_invoices.xlsx'

    # Lists to hold data from all JSON files
    all_containers = []
    all_invoices = []
    all_charges = []

    # Loop through all the JSON files in the input directory
    for filename in os.listdir(input_dir):
        if filename.endswith('.json'):
            file_path = os.path.join(input_dir, filename)

            # Read the JSON file
            with open(file_path, 'r') as file:
                data = json.load(file)

            # Append data to the respective lists
            if "RawInvoiceContainers" in data:
                all_containers.extend(data['RawInvoiceContainers'])

            if "RawInvoices" in data:
                all_invoices.extend(data['RawInvoices'])

            if "RawInvoiceCharges" in data:
                all_charges.extend(data['RawInvoiceCharges'])

    # Convert lists to DataFrames
    df_containers = pd.DataFrame(all_containers)
    df_invoices = pd.DataFrame(all_invoices)
    df_charges = pd.DataFrame(all_charges)

    # Write data to the Excel file, overwriting it if it exists
    with pd.ExcelWriter(output_file, engine='openpyxl', mode='w') as writer:
        df_containers.to_excel(writer, sheet_name='RawInvoiceContainers', index=False)
        df_invoices.to_excel(writer, sheet_name='RawInvoices', index=False)
        df_charges.to_excel(writer, sheet_name='RawInvoiceCharges', index=False)

    print(f'All JSON files have been consolidated into {output_file}.')



def start(input_dir, output_dir, file_name=""):
    if file_name == "":
        for filename in os.listdir(input_dir):
            if filename.endswith('.pdf'):
                pdf_path = os.path.join(input_dir, filename)
                process_file(pdf_path, filename, output_dir)
    else:
        pdf_path = os.path.join(input_dir, file_name)
        process_file(pdf_path, file_name, output_dir)

TYPE1_INPUT_DIR = './input_pdf/type1'
TYPE2_INPUT_DIR = './input_pdf/type2'
TYPE1_OUTPUT_DIR = './output/type1'
TYPE2_OUTPUT_DIR = './output/type2'

if __name__ == "__main__":
    # start(TYPE1_INPUT_DIR, TYPE1_OUTPUT_DIR)
    start(TYPE2_INPUT_DIR, TYPE2_OUTPUT_DIR,'0055010.pdf')
    # make_excel_file()