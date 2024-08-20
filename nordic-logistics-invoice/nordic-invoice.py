import pandas as pd
import pdfplumber
import pytesseract
from PIL import Image, ImageEnhance, ImageFilter
import re

# Regular expressions for each required field
patterns = {
    #"Page": r"Page:\s*(\d+\/\d+)",
    "Invoice": r"Invoice\s(\d+)",
    "Invoice Date": r"Invoice Date:\s*(\d{2}\.\d{2}\.\d{4})",
    "Order No.": r"Order No.:\s*(\d+)",
    "Ext. order no.": r"Ext\. order no\.\s*:\s*(\w+(?:-\w+)?)",
    "Customer Number": r"Customer Number:\s*(\d+)",
    "Loading date": r"Loading date\s*(\d{2}\.\d{2}\.\d{4})",
    "Delivery date": r"Delivery date\s*(\d{2}\.\d{2}\.\d{4})",
    "Vessel Name": r"Vessel Name:\s*(.+?)\sContainer type:",
    "Port of loading": r"Port of loading:\s*\u00A9?\s*(\w+)", 
    "Port of delivery": r"Port of delivery:\s*(\w+)",
    "Total amount without VAT": r"Total amount without VAT\s*((?:\d{1,3}(?:\s?\d{3})*),\d{2} NOK)",
    "Due Date": r"Due Date:\s*(\d{2}\.\d{2}\.\d{4})",
    "Tour No.": r"Tour No.:\s*(\d+)"
}

def initialize_dict(page, invoice_num, invoice_date, due_date, customer_number):
   # List of keys
  keyList = ["Page", "Invoice", "Invoice Date", "Order No.", "Ext. order no.", "Customer Number", "Loading date", "Delivery date", "Vessel Name", "Port of loading"
             , "Port of delivery", "Total amount without VAT", "Due Date", "Tour No." ]
  # initialize dictionary
  d = {}
  # iterating through the elements of list
  for i in keyList:
    d[i] = None
  
  d["Page"] = page
  d["Invoice"] = invoice_num
  d["Invoice Date"]  = invoice_date
  d["Due Date"] = due_date
  d["Customer Number"] = customer_number
  return d

def parse_pdf_via_plumber(input_pdf):
  
  invoice_num = 0
  invoice_date = None
  due_date = None
  customer_number = None
  complete_data = []
  with pdfplumber.open(input_pdf) as pdf:
        pages = pdf.pages
        for i,page in enumerate(pages):
            print("Parsing Page: " + str(i + 1) + " of " + str(len(pages)))
            
            image_bbox = (0, 0, page.width, page.height)
            cropped_page = page.crop(image_bbox)
            image_obj = cropped_page.to_image(resolution=200)
            image_obj.save('input_pdf\\invoice-doc-1.png')
            
            img = Image.open('input_pdf\\invoice-doc-1.png')
            custom_config = r'--oem 1 -l eng --psm 3'
            text = pytesseract.image_to_string(img, config=custom_config)
            # Print the extracted text
            print(f"Page/text {i + 1}:\n{text}\n")

            splitted_text = text.split("Order No.")
            splitted_text_2 = re.split(r'(Order No\.)', text)
            index = 0
            while index < len(splitted_text):
                if splitted_text[index].startswith(":"):
                    splitted_text[index] = "Order No." + splitted_text[index]
                extracted_data = extract_information(splitted_text[index])
                if len(extracted_data) > 0:
                    if  index ==  0:
                        invoice_num = get(extracted_data, 'Invoice')
                        invoice_date = get(extracted_data, 'Invoice Date')
                        due_date = get(extracted_data, 'Due Date')
                        customer_number = get(extracted_data, 'Customer Number')
                    else: 
                        current_invoice = initialize_dict(str(i + 1), invoice_num, invoice_date, due_date, customer_number)
                        current_invoice.update(extracted_data)
                        print(current_invoice)
                        complete_data.append(current_invoice)
                    
                index = index + 1
  
  post_processing(complete_data)                
  return complete_data

def get(extracted_data, key):
    if 'Invoice' in extracted_data.keys():
        return extracted_data[key]


def post_processing(extracted_data):
    delivery_date = None
    for row in extracted_data:
        if row['Delivery date'] is not None:
            delivery_date = row['Delivery date']
        else:
            row['Delivery date'] = delivery_date
            

def extract_information(text):
   # Extracting the information
    extracted_data = {}
    for key, pattern in patterns.items():
        match = re.search(pattern, text)
        if match:
            extracted_data[key] = match.group(1)

    # Print extracted data
    for key, value in extracted_data.items():
        print(f"{key}: {value}")
        
    return extracted_data    

         

extracted_data = parse_pdf_via_plumber('input_pdf\\nordic_3056313_redacted.pdf')            

df = pd.DataFrame(extracted_data)
df.to_csv('invoice_output_data.csv')