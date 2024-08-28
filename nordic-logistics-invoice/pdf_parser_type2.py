import re

class Type2PdfParser:

    # Function to parse individual order blocks
    def parse_order_block_for_invoice(self, invoice_block, block, invoice_base_no, order_index, vat):
        order_data = {}

        reference_no_match = re.search(r"Godsnr\s.*(A.ref\s\d+)", block, re.DOTALL | re.IGNORECASE)
        reference_no = reference_no_match.group(1) if reference_no_match else None
        reference_no = reference_no.strip('\r')

        # Assign the invoice number with order index
        order_data['Invoice No'] = f"{invoice_base_no}/{order_index}"

        # Extract Type
        order_data['Type'] = "Invoice"

        # Extract Invoice Date
        invoice_date_match = re.search(r"Fakturadato\s(\d{1,2}.\d{2}.\d{2,4})", invoice_block, re.DOTALL | re.IGNORECASE)
        order_data['Invoice Date'] = invoice_date_match.group(1) if invoice_date_match else None

        # Extract Bill of Lading
        bol_match = re.search(r"Godsnr\s(.*?)\s", block, re.DOTALL | re.IGNORECASE)
        order_data['Bill of Lading'] = bol_match.group(1) if bol_match else None

        # Use Customer and Customer Address from the invoice block
        customer_match = re.search(r"(.*?)\s\*", invoice_block, re.DOTALL | re.IGNORECASE)
        customer = customer_match.group(1).strip() if customer_match else None

        address_line1_match = re.search(r"\*\s(.*?)\s\*", invoice_block, re.DOTALL | re.IGNORECASE)
        address_line1 = address_line1_match.group(1).strip() if address_line1_match else ""

        address_line2_match = re.search(r"(.*?)\sFakturanr", invoice_block, re.IGNORECASE)
        address_line2 = address_line2_match.group(1).strip() if address_line2_match else ""

        customer_address = f"{address_line1},{address_line2}" if address_line1 else None

        order_data['Customer'] = customer
        order_data['Customer Address'] = customer_address

        # Extract Customer Number
        customer_number_match = re.search(r"Kundenummer\s(\d+)", invoice_block, re.DOTALL | re.IGNORECASE)
        order_data['Customer Number'] = customer_number_match.group(1) if customer_number_match else None

        # Extract ETD
        etd_match = re.search(r"Fra-til..:.*->.*\s(\d{1,2}.\d{1,2}.\d{2,4})", block, re.MULTILINE | re.IGNORECASE)
        order_data['ETD'] = etd_match.group(1) if etd_match else None

        # Extract POL
        pol_match = re.search(r"Fra-til..:(.*)->.*\s\d{1,2}.\d{1,2}.\d{2,4}", block, re.MULTILINE | re.IGNORECASE)
        order_data['POL'] = pol_match.group(1) if pol_match else None

        # Extract POD
        pod_match = re.search(r"Fra-til..:.*->(.*)\s\d{1,2}.\d{1,2}.\d{2,4}", block, re.MULTILINE | re.IGNORECASE)
        order_data['POD'] = pod_match.group(1) if pod_match else None

        # Extract NetValue (excluding currency)
        total_value_match = re.search(r"Oppdragstotal:\s\w{3}\s([\d.]*,\d+)", block, re.MULTILINE | re.IGNORECASE)
        total_value = float(total_value_match.group(1).replace(".", "").replace(",", ".")) if total_value_match else 0.0
        order_data['Total'] = total_value

        # Extract VAT (with * after currency)
        vat_matches = re.findall(r"MOMS\s[\d.]*,\d+\s%\s\w{3}\s([\d.]*,\d+)", block, re.MULTILINE | re.IGNORECASE)
        total_vat = sum(float(vat.replace(".", "").replace(",", ".")) for vat in vat_matches)
        order_data['VAT'] = total_vat

        # Extract Total
        if order_data['Total'] is not None and order_data['VAT'] is not None:
            order_data['NetValue'] = total_value - total_vat
        else:
            order_data['NetValue'] = None

        # Extract Currency
        currency_match = re.search(r"Oppdragstotal:\s(\w{3})\s", block, re.MULTILINE | re.IGNORECASE)
        order_data['Currency'] = currency_match.group(1) if currency_match else "NOK"

        # Extract Reference No.
        order_data['Reference No.'] = reference_no

        # Extract Due Date
        due_date_match = re.search(r"Forfallsdato\s(\d{1,2}.\d{2}.\d{2,4})", invoice_block, re.DOTALL | re.IGNORECASE)
        order_data['Due Date'] = due_date_match.group(1) if due_date_match else None

        # Extract Tour Number
        tour_no_match = re.search(r"Frankatur.*?(\d+/\d+/\w{2,3})", block, re.DOTALL | re.IGNORECASE)
        order_data['Tour Number'] = tour_no_match.group(1) if tour_no_match else None

        return order_data


    def parse_order_block_for_container(self, block, invoice_base_no, order_index, word_block):
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


    def parse_order_block_for_charges(self, block, invoice_base_no, order_index, vat_percentage):

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


    def get_vat(self,text):
        vat_match = re.search(r"(\d+,\d+)\s%\sMOMS", text, re.MULTILINE | re.IGNORECASE)
        vat = float(vat_match.group(1).replace(" ", "").replace(",", ".")) if vat_match else 0.0
        vat = vat / 100
        return vat

    # Function to parse the invoice data
    def parse_invoice_data(self, text):
        invoices = []
        charges = []
        vat = self.get_vat(text)
        invoice_base_no_match = re.search(r"Fakturanr\s(\d+)", text, re.MULTILINE | re.IGNORECASE)
        invoice_base_no = invoice_base_no_match.group(1) if invoice_base_no_match else ''

        order_blocks = re.split(r"Avsender:", text)
        order_index = 1
        for order_block in order_blocks[1:]:
            if order_block.__contains__("Oppdragstotal:"):
                invoice_data = self.parse_order_block_for_invoice(order_blocks[0], "Avsender:" + order_block, invoice_base_no, order_index, vat)
                invoices.append(invoice_data)
                order_index += 1

                # charge_data = self.parse_order_block_for_charges(order_block, invoice_base_no, order_index, vat)
                # charges.extend(charge_data)

        output_data = {
            "RawInvoices": invoices,
            "RawInvoiceCharges": charges
        }

        return output_data