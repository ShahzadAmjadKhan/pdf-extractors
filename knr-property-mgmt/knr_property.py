from multiprocessing import Value
import fitz  # PyMuPDF
import pandas as pd
from collections import OrderedDict

column_names = {}
final_data = []

def initialize_column_names(column_names_line, column_count):
    for x in range(column_count):
        col_name = column_names_line[0][x]
        column_names[col_name] = None
    

def extract_info_from_pdf(pdf_path):
    # Open the PDF file
    pdf_document = fitz.open(pdf_path)
    # Loop through each page in the document
    for page_num in range(pdf_document.page_count):
        print("Parsing Page: " + str(page_num + 1) + " of " + str(pdf_document.page_count))
        page = pdf_document.load_page(page_num)
        page_data = get_page_data(page, page_num)

        
    return final_data

   
def get_page_data(page, page_num):
    tabs = page.find_tables()
    #print(f"{len(tabs.tables)} table(s) on {page}")
    tab = tabs[0]
    column_names_line = tab.extract()
    
    if page_num == 0 :
        initialize_column_names(column_names_line, tab.col_count)
        
    for x in range(tab.row_count):
        current_row_data = {}
        if x == 0:
            continue
        single_row = column_names_line[x]
        index = 0
        enrich_data(single_row)
        for x in column_names:
            current_row_data[x] = single_row[index]
            index = index + 1
        final_data.append(current_row_data)
    

def enrich_data(row):
    if str(row[0]).startswith("Total"):
        splitted_row = str(row[0]).split(" ")
        row[0] = splitted_row[0]
        row[5] = splitted_row[1]
        row[6] = splitted_row[2]
    
# Path to your PDF file
pdf_path = 'input_pdf\\knr-property-owner-statement.pdf'
extracted_data = extract_info_from_pdf(pdf_path)

df = pd.DataFrame(extracted_data)
df.to_csv('knr_statement_output_data.csv')