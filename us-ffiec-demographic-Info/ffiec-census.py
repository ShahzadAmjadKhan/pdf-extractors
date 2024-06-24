from multiprocessing import Value
import fitz  # PyMuPDF
import pandas as pd
from collections import OrderedDict

columns_names_with_coord = OrderedDict()

def initialize_dict():
  d = {}
  for key, value in columns_names_with_coord.items():
    d[value] = None

  return d

def extract_info_from_pdf(pdf_path):
    # Open the PDF file
    pdf_document = fitz.open(pdf_path)
    final_data = []
    # Loop through each page in the document
    for page_num in range(pdf_document.page_count):
        print("Parsing Page: " + str(page_num + 1) + " of " + str(pdf_document.page_count))
        page = pdf_document.load_page(page_num)
        text = page.get_text("text")

        if page_num == 0:
            get_table_header_row(page)
        current_census_row = initialize_dict()

        #print_block_text(page)
        #check_font(page)
        dict = page.get_text("dict")
        blocks = dict["blocks"]
        for block in blocks:
            current_census_row = initialize_dict()
            if "lines" in block.keys():
                spans = block['lines']
                for span in spans:
                    data = span['spans']
                    for lines in data:
                        font = lines['font'] 
                        if font == 'Arial' : 
                            #read_line.append(lines['text'] + ";" + str(lines['bbox']))
                            column_name = get_column_name(lines['bbox'][0])
                            current_census_row[column_name] = lines['text']
            if current_census_row['County Code']:
                final_data.append(current_census_row)
                        
    return final_data

def get_column_name(data_coordinate):
   previous_column_value = ''
   for header_column_coord, column_name in columns_names_with_coord.items():
        #print(header_column_coord, column_name)
        if data_coordinate < header_column_coord:
            return previous_column_value
        else:
            previous_column_value = column_name
   return previous_column_value     
    
   
def get_table_header_row(page):
    tabs = page.find_tables()
    #print(f"{len(tabs.tables)} table(s) on {page}")
    tab = tabs[0]
    #print(tab.cells[0][0])  print(tab.cells[1][0])     print(tab.cells[2][0])     print(tab.cells[3][0])     print(tab.cells[4][0])
    column_names_line = tab.extract()
    #print(column_names_line)
    
    for x in range(tab.col_count):
        col_name = column_names_line[0][x]
        if col_name == '':
            continue
        columns_names_with_coord[tab.cells[x][0]] =  str(col_name).replace('\n', ' ')

    #print(columns_names_with_coord)
    #for line in tab.extract():  # print cell text for each row
    #    print(line)

def print_block_text(page):
  results = []
  dict = page.get_text("dict")
  blocks = dict["blocks"]
  for block in blocks:
    #if block['number'] < 31:
     #   continue
    block_number = str(block['number'])
    block_coord = prev_read_coord = block['bbox']
    
    read_line = []
    if "lines" in block.keys():
        spans = block['lines']
        for span in spans:
            data = span['spans']
            for lines in data:
                read_line.append(lines['text'] + ";" + str(lines['bbox']))
    block_text = read_line
    results.append((block_number, block_coord, block_text))
    
  df = pd.DataFrame(results)
  df.to_csv('final-coord.csv')
    

def check_font(page):
  results = []
  results_dict = {}
  prev_read_line = ''
  prev_read_coord = None
  headings = []
  dict = page.get_text("dict")
  blocks = dict["blocks"]
  for block in blocks:
    if block['number'] < 31:
        continue
    print('Processing ' + str(block['number'])) 
    print(block['lines'])
    if "lines" in block.keys():
        print(block['bbox'])
        print(prev_read_coord)
       
        if prev_read_coord is None:
            prev_read_coord = block['bbox'][0]
            
        if part_of_same_heading(block['bbox'][0], prev_read_coord) == True:
            print ('Same heading')
        else: 
            headings.append(prev_read_line)   
            prev_read_line = ''
            prev_read_coord = block['bbox'][0]
            
        spans = block['lines']
        for span in spans:
            data = span['spans']
            for lines in data:
                prev_read_line += lines['text']
                font_size = round(float(lines['size'])  , 2)
                font_color = lines['color'] 
                font = lines['font']
                if font == 'Arial,Bold'or (font_size == 9.8 and font_color == 16777215) : 
                   results_dict[lines['text']] = font_size
                #if keyword in lines['text'].lower(): # only store font information of a specific keyword
                results.append((lines['text'], lines['size'], lines['font'], lines['color'], block['bbox'][0]))
                
  return results_dict 

def part_of_same_heading(new_coord, prev_coord):
    diff = float(prev_coord) - float(new_coord)
    if diff > 20:
      return False
    else:
        return True    

# Path to your PDF file
pdf_path = 'input_pdf\\MSA_MD- 11244 - ANAHEIM-SANTA ANA-IRVINE, CA.pdf'
extracted_data = extract_info_from_pdf(pdf_path)

df = pd.DataFrame(extracted_data)
df.to_csv('output_table_us_ffiec_demographic_Info.csv')