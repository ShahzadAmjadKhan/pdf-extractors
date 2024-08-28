import os
from function_app import *
import pandas as pd

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
    make_excel_file()