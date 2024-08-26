import re
import json
import base64

# Function to parse individual order blocks
def parse_order_block_for_invoice(invoice_block, block, invoice_base_no, order_index, vat, base64_string):
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
    bol_match = re.search(r"Invoice reference:\s([\w\s,-/，]*)[\s]*Tour No.|Ext. order no.: ([\w\s,-/，]*)[\s]*Tour No.|Invoice reference:\s([\w,-/]*)\n|Ext. order no.: ([\w\s,-/]*)\n", block, re.MULTILINE | re.IGNORECASE)
    if bol_match is None:
        bol_line = get_bill_of_landing(base64_string, reference_no)
        bol_match = re.search(r"Invoice reference:\s([\w\s,-/，]*)[\s]*Tour No.|Ext. order no.: ([\w\s,-/，]*)[\s]*Tour No.|Invoice reference:\s([\w,-/]*)\n|Ext. order no.: ([\w\s,-/]*)\n", bol_line, re.MULTILINE | re.IGNORECASE)

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
    eta_match = re.search(r"Loading date (\d{2}\.\d{2}\.\d{4})", block, re.MULTILINE | re.IGNORECASE)
    eta = eta_match.group(1) if eta_match else None
    if eta is None:
        eta = get_loading_date(base64_string, reference_no)
    order_data['ETA'] = eta

    # Extract ETD
    etd_match = re.search(r"Delivery date (\d{2}\.\d{2}\.\d{4})", block, re.MULTILINE | re.IGNORECASE)
    order_data['ETD'] = etd_match.group(1) if etd_match else None

    # Extract Vessel/Voyage
    vessel_voyage_match = re.search(r"Vessel name:\s*(.+?)\s+Container type:", block, re.MULTILINE | re.IGNORECASE)
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
    vat_matches = re.findall(r"([\d\s,]+) \w{3} \*", block, re.MULTILINE | re.IGNORECASE)
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
    tour_no_match = re.search(r"Tour No.: (\d+)", block, re.MULTILINE | re.IGNORECASE)
    if tour_no_match is None:
        tour_no_match = re.search(r"Tour No.: (\d+)", bol_line, re.MULTILINE | re.IGNORECASE)
    order_data['Tour Number'] = tour_no_match.group(1) if tour_no_match else None

    return order_data


def get_bill_of_landing(base64_string, order_no):
    return "Order No.: 786308 Ext. order no.: KO2100653,KO2100612,KO2100474,KO2100652,KO2100252 Tour No.: 328641 Consignment: 786308.1 Ningbo Home-Dollar Imp. & Exp. NILLE AS CN NINGBO N 1540 Vestby Loading date 26.02.2022 Delivery date 08.04.2022 Incoterms: FOB Shipment Mode: DEEPSEA Sender: Receiver: Port of loading: Vessel Name: Port of delivery: - NOMSS CNNBG Container no.: EISU8491488 Container type: 40HC F-weight Quantity Content A-weight Loading meter Volume Package STP 8154,5 1 604 0,00 Carton 63,095 8154,5 0 8154,5 0,00 63,095 8154,5 0 16700 8,9363 NOK 149 236,21 NOK"

def get_loading_date(base64_string, order_no):
    eta_match = re.search(r"Loading date (\d{2}\.\d{2}\.\d{4})",base64.b64decode(base64_string.encode('utf-8')).decode('utf-8') , re.IGNORECASE)
    eta = eta_match.group(1) if eta_match else None
    return eta

def parse_order_block_for_container(block, invoice_base_no, order_index):
    container_data = {}
    container_data['Invoice'] = f"{invoice_base_no}/{order_index}"

    container_no_match = re.search(r"Container no.: (\w+)", block, re.MULTILINE | re.IGNORECASE)
    container_data['Container ID'] = container_no_match.group(1) if container_no_match else None

    container_no_type = re.search(r"Container type: (\w+)", block, re.MULTILINE | re.IGNORECASE)
    container_data['Type'] = container_no_type.group(1) if container_no_type else None
    
    return container_data


def parse_order_block_for_charges(block, invoice_base_no, order_index, vat_percentage):

    charges = []
    charge_data = {}

    charges_text_match = re.search(r"Volume(.*)Total amount without VAT", block, re.DOTALL|re.IGNORECASE)
    charges_text = charges_text_match.group(1) if charges_text_match else None
    charges_lines = charges_text.splitlines()

    for index, line in enumerate(charges_lines):
        charge_data['Invoice'] = f"{invoice_base_no}/{order_index}"
        currency_match = re.search(r"\d{1,3}(?: \d{3})*,\d{2}\s+(\w{3})", line)
        currency = currency_match.group(1) if currency_match else None
        if currency is not None:
            if line.endswith(currency) or line.endswith(currency + " *"):
                charge_type_match = re.match(r"(.*?)\d+\s*\d+,\d+\s"+currency, line)
                charge_type = charge_type_match.group(1) if charge_type_match else None
                charge_type = charge_type.rstrip(' ')
                # if charge_type is None:
                #     charge_type_match = re.match(r"^(.*?)(?=\s+\d)", line)
                #     charge_type = charge_type_match.group(1) if charge_type_match else None
                if charge_type.endswith("/"):
                    next_line = charges_lines[index+1]
                    charge_type = charge_type + " " + next_line

                unit_price_matches = re.findall(r"(\d+\s*\d+,\d+)\s"+currency, line)
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
                    total = unit_price

                vat_match = re.search(r"([\d\s,]+) \w{3} \*", line)
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


def extract_and_convert_prices(text):
    # Regex pattern to match numbers with optional space and comma
    pattern = r'^.*?(?=\s+\d)(.*)\w{3}'

    # Find all matches in the text
    match = re.search(pattern, text)
    price = match.group(1)

    # Convert matched prices to float
    converted_prices = float(price.replace(' ', '').replace(',', '.'))

    return converted_prices


def get_vat(text):
    vat_match = re.search(r"(\d+,\d+) % VAT", text, re.MULTILINE | re.IGNORECASE)
    vat = float(vat_match.group(1).replace(" ", "").replace(",", ".")) if vat_match else 0.0
    vat = vat / 100
    return vat

# Function to parse the invoice data
def parse_invoice_data(text, base64_string):
    invoices = []
    containers = []
    charges = []
    vat = get_vat(text)

    # Split the text into invoice blocks using the "Invoice \d+ from dd.dd.dddd" pattern
    invoice_blocks = re.split(r"Invoice (\d+) from \d{2}\.\d{2}\.\d{4}", text, re.IGNORECASE)

    for i in range(1, len(invoice_blocks), 2):
        invoice_base_no = invoice_blocks[i]  # Get the invoice number
        invoice_content = invoice_blocks[i + 1]

        # Split further into order blocks based on "Order No.:"
        order_blocks = re.split(r"Order No\.:", invoice_content)

        for order_index, order_block in enumerate(order_blocks[1:], 1):
            invoice_data = parse_order_block_for_invoice(invoice_blocks[0], "Order No.:" + order_block, invoice_base_no, order_index, vat, base64_string)
            invoices.append(invoice_data)

            container_data = parse_order_block_for_container(order_block, invoice_base_no, order_index)
            containers.append(container_data)

            charge_data = parse_order_block_for_charges(order_block, invoice_base_no, order_index, vat)
            charges.extend(charge_data)

    output_data = {
        "RawInvoiceContainers": containers,
        "RawInvoices": invoices,
        "RawInvoiceCharges": charges
    }

    return output_data

# Read the input text
with open('./input_pdf/pdfplumper_input.txt', 'r') as file:
    input_text = file.read()

base64_string = base64.b64encode('Loading date 01.03.2024'.encode('utf-8')).decode('utf-8')

# Parse the invoice data
data = parse_invoice_data(input_text, base64_string)

# Write the output JSON to a file
with open('./output/output.json', 'w') as json_file:
    json.dump(data, json_file, indent=2)

print("Parsing complete. JSON data saved to ./output/output.json.")
