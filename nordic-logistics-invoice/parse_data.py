import os
from function_app import *
import pandas as pd


def process_file(pdf_path, filename, output_dir):
    with open(pdf_path, 'rb') as pdf_file:
        pdf_data = pdf_file.read()
        base64_string = base64.b64encode(pdf_data).decode('utf-8')

    input_stream = io.BytesIO(pdf_data)
    # Parse the invoice data
    data = parse_pdf(input_stream, base64.b64decode(base64_string))

    # Define the output JSON file name
    json_filename = os.path.splitext(filename)[0] + '.json'

    # Write the output JSON to a file in the output directory
    with open(os.path.join(output_dir, json_filename), 'w') as json_file:
        json.dump(data, json_file, indent=2)

    print(f'Parsed {filename} and saved to {json_filename}')


def make_excel_file(input_dir, output_dir, filename="all_invoices.xlsx"):
    # Lists to hold data from all JSON files
    all_containers = []
    all_invoices = []
    all_charges = []

    output_file = os.path.join(output_dir, filename)

    # Loop through all the JSON files in the input directory
    for filename in os.listdir(input_dir):
        if filename.endswith('.json'):
            file_path = os.path.join(input_dir, filename)

            # Read the JSON file
            with open(file_path, 'r') as file:
                data = json.load(file)

            if "RawInvoices" in data:
                for item in data['RawInvoices']:
                    item['file_name'] = filename  # Add the filename to each record
                all_invoices.extend(data['RawInvoices'])

            if "RawInvoiceCharges" in data:
                for item in data['RawInvoiceCharges']:
                    item['file_name'] = filename  # Add the filename to each record
                all_charges.extend(data['RawInvoiceCharges'])

            # Append data to the respective lists, including the filename
            if "RawInvoiceContainers" in data:
                for item in data['RawInvoiceContainers']:
                    item['file_name'] = filename  # Add the filename to each record
                all_containers.extend(data['RawInvoiceContainers'])

    # Convert lists to DataFrames
    df_invoices = pd.DataFrame(all_invoices)
    df_charges = pd.DataFrame(all_charges)
    df_containers = None
    if len(all_containers) > 0:
        df_containers = pd.DataFrame(all_containers)


# Write data to the Excel file, overwriting it if it exists
    with pd.ExcelWriter(output_file, engine='openpyxl', mode='w') as writer:
        df_invoices.to_excel(writer, sheet_name='RawInvoices', index=False)
        df_charges.to_excel(writer, sheet_name='RawInvoiceCharges', index=False)
        if df_containers is not None:
            df_containers.to_excel(writer, sheet_name='RawInvoiceContainers', index=False)


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
    start(TYPE1_INPUT_DIR, TYPE1_OUTPUT_DIR)
    make_excel_file(TYPE1_OUTPUT_DIR, TYPE1_OUTPUT_DIR, 'type1_all_invoices.xlsx')

    start(TYPE2_INPUT_DIR, TYPE2_OUTPUT_DIR)
    make_excel_file(TYPE2_OUTPUT_DIR, TYPE2_OUTPUT_DIR, 'type2_all_invoices.xlsx')