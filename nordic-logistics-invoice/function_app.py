import azure.functions as func
import pdfplumber
import re
import logging
import json
import base64
import io

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
    word_text = parse_pdf_via_plumber_and_use_words(input_stream, pdf_data_base64)
    output_data = parse_invoice_data(text,  word_text)
    return output_data


# Function to parse individual order blocks
def parse_order_block_for_invoice(invoice_block, block, invoice_base_no, order_index, vat, word_block):
    order_data = {}

    reference_no_match = re.search(r"Order No.: (\d+)", block, re.MULTILINE | re.IGNORECASE)
    reference_no = reference_no_match.group(1) if reference_no_match else None

    # Assign the invoice number with order index
    order_data['Invoice No'] = f"{invoice_base_no}/{order_index}"

    # Extract Type
    order_data['Type'] = "Invoice"

    # Extract Invoice Date
    invoice_date_match = re.search(r"Invoice date: (\d{2}\.\d{2}\.\d{4})", invoice_block, re.MULTILINE | re.IGNORECASE)
    order_data['Invoice Date'] = invoice_date_match.group(1) if invoice_date_match else None

    # Extract Bill of Lading
    bol_pattern = r"Invoice reference:\s(.*?)[\s]*Tour No.|Ext. order no.: (.*?)[\s]*Tour No."
    bol_match = re.search(bol_pattern, block, re.MULTILINE | re.IGNORECASE)
    if bol_match is None:
        bol_match = re.search(bol_pattern, word_block, re.MULTILINE | re.IGNORECASE)

    if bol_match is None:
        bol_pattern2 = r"Invoice reference:\s(.*?)\n|Ext. order no.: (.*?)\n"
        bol_match = re.search(bol_pattern2, block, re.MULTILINE | re.IGNORECASE)
        if bol_match is None:
            bol_match = re.search(bol_pattern2, word_block, re.MULTILINE | re.IGNORECASE)


    if bol_match.group(1) is not None:
        order_data['Bill of Lading'] = bol_match.group(1).strip("\n").strip(" ")
    elif bol_match.group(2) is not None:
        order_data['Bill of Lading'] = bol_match.group(2).strip("\n").strip(" ")
    elif bol_match.group(3) is not None:
        order_data['Bill of Lading'] = bol_match.group(3).strip("\n").strip(" ")
    elif bol_match.group(4) is not None:
        order_data['Bill of Lading'] = bol_match.group(4).strip("\n").strip(" ")
    else:
        order_data['Bill of Lading'] = ''
    # Use Customer and Customer Address from the invoice block
    customer_match = re.search(r"^(.*?)\s+Customer number:", invoice_block, re.MULTILINE | re.IGNORECASE)
    customer = customer_match.group(1).strip() if customer_match else None

    address_line1_match = re.search(r"(.*?)\s+Your VAT ID no\.:", invoice_block, re.MULTILINE | re.IGNORECASE)
    address_line1 = address_line1_match.group(1).strip() if address_line1_match else ""

    address_line2_match = re.search(r"(.*?)\s+Email:", invoice_block, re.MULTILINE | re.IGNORECASE)
    address_line2 = address_line2_match.group(1).strip() if address_line2_match else ""

    address_line3_match = re.search(r"(.*?)\s+Page: \d+", invoice_block, re.MULTILINE | re.IGNORECASE)  # Page number is not needed for address
    address_line3 = address_line3_match.group(1).strip() if address_line3_match else ""

    customer_address = f"{address_line1},{address_line2},{address_line3}" if address_line1 else None

    order_data['Customer'] = customer
    order_data['Customer Address'] = customer_address

    # Extract Customer Number
    customer_number_match = re.search(r"Customer number: (\d+)", invoice_block, re.MULTILINE | re.IGNORECASE)
    order_data['Customer Number'] = customer_number_match.group(1) if customer_number_match else None

    # Extract ETA
    eta_pattern = r"Loading date (\d{2}\.\d{2}\.\d{4})"
    eta_match = re.search(eta_pattern, block, re.MULTILINE | re.IGNORECASE)
    if eta_match is None:
        eta_match = re.search(eta_pattern, word_block, re.MULTILINE | re.IGNORECASE)
    eta = eta_match.group(1) if eta_match else None
    order_data['ETA'] = eta

    # Extract ETD
    etd_pattern = r"Delivery date (\d{2}\.\d{2}\.\d{4})"
    etd_match = re.search(etd_pattern, block, re.MULTILINE | re.IGNORECASE)
    if etd_match is None:
        etd_match = re.search(etd_pattern, word_block, re.MULTILINE | re.IGNORECASE)
    etd = etd_match.group(1) if etd_match else None
    order_data['ETD'] = etd

    # Extract Vessel/Voyage
    vessel_voyage_match = re.search(r"Vessel name:\s*(.+?)\s*Container type:", block, re.MULTILINE | re.IGNORECASE)
    if vessel_voyage_match is None:
        vessel_voyage_match = re.search(r"Vessel name:\s*Port of delivery: (.+?)\w{5}\s*\w{5}\s*Container no.:", word_block, re.MULTILINE | re.IGNORECASE)

    order_data['Vessel/Voyage'] = vessel_voyage_match.group(1).strip() if vessel_voyage_match else None

    # Extract POL
    pol_match = re.search(r"Port of loading: (\w+)", block, re.MULTILINE | re.IGNORECASE)
    order_data['POL'] = pol_match.group(1) if pol_match else None

    # Extract POD
    pod_match = re.search(r"Port of delivery: (\w+)", block, re.MULTILINE | re.IGNORECASE)
    order_data['POD'] = pod_match.group(1) if pod_match else None

    # Extract NetValue (excluding currency)
    net_value_match = re.search(r"Total amount without VAT ([\d\s,]+)", block, re.MULTILINE | re.IGNORECASE)
    order_data['NetValue'] = float(net_value_match.group(1).replace(" ", "").replace(",", ".")) if net_value_match else None

    # Extract VAT (with * after currency)
    vat_matches = re.findall(r"\s+([\d\s,]+) \w{3} \*", block, re.MULTILINE | re.IGNORECASE)
    total_vat = sum(float(vat.replace(" ", "").replace(",", ".")) for vat in vat_matches)
    order_data['VAT'] = total_vat * vat

    # Extract Total
    if order_data['NetValue'] is not None and order_data['VAT'] is not None:
        order_data['Total'] = order_data['NetValue'] + order_data['VAT']
    else:
        order_data['Total'] = None

    # Extract Currency
    currency_match = re.search(r"Total amount without VAT [\d\s,]+ ([A-Z]{3})", block, re.MULTILINE | re.IGNORECASE)
    order_data['Currency'] = currency_match.group(1) if currency_match else "NOK"

    # Extract Reference No.
    order_data['Reference No.'] = reference_no

    # Extract Due Date
    due_date_match = re.search(r"Due date: (\d{2}\.\d{2}\.\d{4})", invoice_block, re.MULTILINE | re.IGNORECASE)
    order_data['Due Date'] = due_date_match.group(1) if due_date_match else None

    # Extract Tour Number
    tour_pattern = r"Tour No.: (\d+)"
    tour_no_match = re.search(tour_pattern, block, re.MULTILINE | re.IGNORECASE)
    if tour_no_match is None:
        tour_no_match = re.search(tour_pattern, word_block, re.MULTILINE | re.IGNORECASE)

    order_data['Tour Number'] = tour_no_match.group(1) if tour_no_match else None

    return order_data


def parse_order_block_for_container(block, invoice_base_no, order_index, word_block):
    container_data = {}
    container_data['Invoice'] = f"{invoice_base_no}/{order_index}"

    container_no_match = re.search(r"Container no.: (\w+)", block, re.MULTILINE | re.IGNORECASE)
    container_data['Container ID'] = container_no_match.group(1) if container_no_match else None

    container_no_pattern = r"Container type: (\w+)"
    container_no_type = re.search(container_no_pattern, block, re.MULTILINE | re.IGNORECASE)
    if container_no_type is None:
        container_no_type = re.search(container_no_pattern, word_block, re.MULTILINE | re.IGNORECASE)

    container_data['Type'] = container_no_type.group(1) if container_no_type else None

    return container_data


def parse_order_block_for_charges(block, invoice_base_no, order_index, vat_percentage):

    charges = []
    charge_data = {}
    currency_match = re.search(r"Total amount without VAT [\d\s,]+ ([A-Z]{3})", block, re.MULTILINE | re.IGNORECASE)
    total_currency = currency_match.group(1) if currency_match else "NOK"
    total_value_blocks = re.split(r"Total amount without VAT [\d\s,]+"+total_currency, block, re.MULTILINE | re.IGNORECASE)
    charges_lines = total_value_blocks[0].splitlines()

    for index, line in enumerate(charges_lines):
        charge_data['Invoice'] = f"{invoice_base_no}/{order_index}"
        if total_currency is not None:
            if line.endswith(total_currency) or line.endswith(total_currency + " *"):
                charge_type_match = re.match(r"(.*?)\s[\d\s]*\d+,\d+\s"+total_currency, line)
                charge_type = charge_type_match.group(1) if charge_type_match else None
                charge_type = charge_type.rstrip(' ')
                if charge_type.endswith("/") and index + 1 <= len(charges_lines):
                    next_line = charges_lines[index+1]
                    charge_type = charge_type + " " + next_line

                unit_price_matches = re.findall(r"\s([\d\s]*\d+,\d+)\s"+total_currency, line)
                if len(unit_price_matches) == 2:
                    unit_price = float(unit_price_matches[0].split(' ')[0])
                    currency = 'USD'
                    exchange_rate = unit_price_matches[0].split(' ')[1]
                    exchange_rate = float(exchange_rate.replace(' ', '').replace(',', '.'))
                    total = unit_price_matches[1] if unit_price_matches[1] else '0.0'
                    total = float(total.replace(' ', '').replace(',', '.'))
                else:
                    unit_price = unit_price_matches[0] if unit_price_matches[0] else 0.0
                    unit_price = float(unit_price.replace(' ', '').replace(',', '.'))
                    exchange_rate = 1.0000
                    currency = total_currency
                    total = unit_price

                vat_match = re.search(r"\s+([\d\s,]+) \w{3} \*", line)
                vat_amount = float(vat_match.group(1).replace(" ", "").replace(",", ".")) if vat_match else 0.0
                final_vat = vat_amount * vat_percentage

                charge_data['Charge Type'] = charge_type.strip(' ')
                charge_data['Unit Price'] = unit_price
                charge_data['Currency'] = currency
                charge_data['Exchange Rate'] = exchange_rate
                charge_data['Total'] = total + final_vat
                charge_data['Currency Total'] = 'NOK'
                charge_data['VAT'] = final_vat
                if vat_amount > 0.0:
                    charge_data['VAT Percentage'] = str(vat_percentage * 100) + '%'
                charges.append(charge_data)
                charge_data = {}

    return charges


def get_vat(text):
    vat_match = re.search(r"(\d+,\d+) % VAT", text, re.MULTILINE | re.IGNORECASE)
    vat = float(vat_match.group(1).replace(" ", "").replace(",", ".")) if vat_match else 0.0
    vat = vat / 100
    return vat

# Function to parse the invoice data
def parse_invoice_data(text, word_text):
    invoices = []
    containers = []
    charges = []
    vat = get_vat(text)

    # Split the text into invoice blocks using the "Invoice \d+ from dd.dd.dddd" pattern
    invoice_blocks = re.split(r"Invoice (\d+) from \d{2}\.\d{2}\.\d{4}", text, re.IGNORECASE)
    word_invoice_blocks = re.split(r"Invoice (\d+) from \d{2}\.\d{2}\.\d{4}", word_text, re.IGNORECASE)

    for i in range(1, len(invoice_blocks), 2):
        invoice_base_no = invoice_blocks[i]  # Get the invoice number
        invoice_content = invoice_blocks[i + 1]
        word_invoice_content = word_invoice_blocks[i + 1]

        # Split further into order blocks based on "Order No.:"
        order_blocks = re.split(r"Order No\.:", invoice_content)
        word_order_blocks = re.split(r"Order No\.:", word_invoice_content)

        for order_index, order_block in enumerate(order_blocks[1:], 1):
            invoice_data = parse_order_block_for_invoice(invoice_blocks[0], "Order No.:" + order_block, invoice_base_no, order_index, vat, word_order_blocks[order_index])
            invoices.append(invoice_data)

            container_data = parse_order_block_for_container(order_block, invoice_base_no, order_index, word_order_blocks[order_index])
            containers.append(container_data)

            charge_data = parse_order_block_for_charges(order_block, invoice_base_no, order_index, vat)
            charges.extend(charge_data)

    output_data = {
        "RawInvoiceContainers": containers,
        "RawInvoices": invoices,
        "RawInvoiceCharges": charges
    }

    return output_data