import re
import json
import io

# Function to parse individual order blocks
def parse_order_block_for_invoice(invoice_block, block, invoice_base_no, order_index, vat, input_stream):
    order_data = {}

    # Assign the invoice number with order index
    order_data['Invoice No'] = f"{invoice_base_no}/{order_index}"

    # Extract Type
    order_data['Type'] = "Invoice"

    # Extract Invoice Date
    invoice_date_match = re.search(r"Invoice date: (\d{2}\.\d{2}\.\d{4})", invoice_block, re.MULTILINE | re.IGNORECASE)
    order_data['Invoice Date'] = invoice_date_match.group(1) if invoice_date_match else None

    # Extract Bill of Lading
    bol_match = re.search(r"Invoice reference: ([\w,]+)|Ext. order no.: ([\w,]+)", block, re.MULTILINE | re.IGNORECASE)
    if bol_match.group(1) is not None:
        order_data['Bill of Lading'] = bol_match.group(1)
    else:
        order_data['Bill of Lading'] = bol_match.group(2)

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

    reference_no_match = re.search(r"Order No.: (\d+)", block, re.MULTILINE | re.IGNORECASE)
    reference_no = reference_no_match.group(1) if reference_no_match else None

    # Extract ETA
    eta_match = re.search(r"Loading date (\d{2}\.\d{2}\.\d{4})", block, re.MULTILINE | re.IGNORECASE)
    eta = eta_match.group(1) if eta_match else None
    if eta is None:
        eta = get_loading_date(input_stream, reference_no)
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
    order_data['Tour Number'] = tour_no_match.group(1) if tour_no_match else None

    return order_data


def get_loading_date(input_stream, order_no):
    eta_match = re.search(r"Loading date (\d{2}\.\d{2}\.\d{4})", input_stream.readline(), re.IGNORECASE)
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

    charge_types = ["Vareavgift", "BL dokumentasjon", "Fortolling", "THC", "SECA", "Seafreight", "Consolidation fee", "Port dues", "Rail"]
    charges = []
    charge_data = {}

    charges_text_match = re.search(r"Volume(.*)Total amount without VAT", block, re.DOTALL|re.IGNORECASE)
    charges_text = charges_text_match.group(1) if charges_text_match else None
    charges_lines = charges_text.splitlines()

    for line in charges_lines:
        charge_data['Invoice']= f"{invoice_base_no}/{order_index}"
        if line.startswith(tuple(charge_types)):
            charge_type_match = re.match(r"^(.*?)(?=\s+\d)", line)
            charge_type = charge_type_match.group(1) if charge_type_match else None
            if charge_type.__contains__("USD"):
                charge_type = charge_type.split(" ")[0]
                unit_price_match = re.search(r"\s(\d+)\s", line)
                unit_price = unit_price_match.group(1) if unit_price_match else 0.0
                unit_price = float(unit_price)
                currency = 'USD'
                exchange_rate_match = re.search(r"\b(\d+\s*,\d+)", line)
                exchange_rate = exchange_rate_match.group(1) if exchange_rate_match else "0.0"
                exchange_rate = float(exchange_rate.replace(' ', '').replace(',', '.'))
                total_match = re.search(r"\s\d+\s\d+,\d+\s\w{3}\s(\d+\s*\d+,\d+)", line)
                total = total_match.group(1) if total_match else "0.0"
                total = float(total.replace(' ', '').replace(',', '.'))
            else:
                unit_price = extract_and_convert_prices(line)
                currency_match = re.search(r"\d{1,3}(?: \d{3})*,\d{2}\s+(\w{3})", line)
                currency = currency_match.group(1) if currency_match else None
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
def parse_invoice_data(text, input_stream):
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
            invoice_data = parse_order_block_for_invoice(invoice_blocks[0], "Order No.:" + order_block, invoice_base_no, order_index, vat, input_stream)
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

text = 'Loading date 01.03.2024'
input_stream = io.StringIO(text)

# Parse the invoice data
data = parse_invoice_data(input_text, input_stream)

# Write the output JSON to a file
with open('./output/output.json', 'w') as json_file:
    json.dump(data, json_file, indent=2)

print("Parsing complete. JSON data saved to ./output/output.json.")
