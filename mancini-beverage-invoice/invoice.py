from multiprocessing import Value
import fitz  # PyMuPDF
import pandas as pd
import pdfplumber
import pytesseract
from PIL import Image, ImageEnhance, ImageFilter

po_box_text = ""
sold_to_text = ""

def draw_table_with_plumber(pdf_path, page): 
    extracted_table = []
    with pdfplumber.open(pdf_path) as pdf:
        pages = pdf.pages
        explicit_horizontal_lines = []
        if page.page_number == 1:
            explicit_horizontal_lines = [0.5]
        explicit_vertical_lines = []
        for i,page in enumerate(pages):
            text = page.extract_text(keep_blank_chars=True)
            #print(text)
            rows = page.search('PRICE')
            if len(rows) > 0:
                row = rows[0]
                coord = row['bottom']
            else:
                coord = 7
            
            j = 1
            coord = coord +  7
            explicit_horizontal_lines.append(coord)
            coord = coord + 6
            explicit_horizontal_lines.append(coord)
            while j < 20:
                coord = coord + 3.5 # 6 is charachter height, and 3.5 is distance between 2 vertical characters
                explicit_horizontal_lines.append(coord)
                coord = coord + 6
                explicit_horizontal_lines.append(coord)
                j = j + 1
                
            #print(text)
            explicit_vertical_lines = [5, 37, 74, 82.7, 102, 139, 176, 320, 400, 448, 488, 528, 612, 654 ] # for total  4 is character width,
            table_settings = { "horizontal_strategy": "explicit", "vertical_strategy": "explicit",
                               "explicit_horizontal_lines": explicit_horizontal_lines, "explicit_vertical_lines": explicit_vertical_lines, "snap_tolerance": 3.5}
            
            
            im = page.to_image(300)
            #imtable = im.reset().debug_tablefinder()
            imtable = im.reset().debug_tablefinder(table_settings)
            #imtable.show()
            table = page.extract_tables(table_settings)
            for row in table:
                extracted_table = row
                #print(row)
    return extracted_table

def ocr_image(image_name):
    image_path = 'input_pdf\\' + image_name
    img = Image.open(image_path)
    custom_config = r'--oem 1 -l eng --psm 3'
    text = pytesseract.image_to_string(img, config=custom_config)
    #print(f"{image_name} :\n{text}\n")
    print("Image: " + image_name + " created for ocr text extraction." )
    return text

def create_image(page, image_name, image_bbox, _resolution):
    image_path = 'input_pdf\\' + image_name
    cropped_page = page.crop(image_bbox)
    image_obj = cropped_page.to_image(resolution=_resolution)
    image_obj.save(image_path)

def get_po_box(page):
    image_name = 'po_box.png'
    image_bbox = (35, 60, 256, 80)
    resolution = 200
    create_image(page, image_name, image_bbox, 200)
    text = ocr_image(image_name)
    return text

def get_sold_to(page):
    image_name = 'sold_to.png'
    image_bbox = (20, 85, 256, 160)
    resolution = 200
    create_image(page, image_name, image_bbox, 200)
    text = ocr_image(image_name)
    return text

def get_line_items(page):
    ## complete
    image_name = 'line_items.png'
    image_bbox = (20, 180, 675, 385)
    resolution = 300
    create_image(page, image_name, image_bbox, resolution)
    text = ocr_image(image_name)

    #pdf = pytesseract.image_to_pdf_or_hocr('input_pdf\\line_items_unit_disc.png', extension='pdf')
    pdf = pytesseract.image_to_pdf_or_hocr('input_pdf\\line_items.png', extension='pdf', config = " -c tessedit_create_pdf=1")
    with open('input_pdf\\line_items.pdf', 'w+b') as f:
        f.write(pdf) # pdf type is bytes by default
    extracted_table = draw_table_with_plumber('input_pdf\\line_items.pdf', page)
    print("Line items data extracted successfully." )
    return extracted_table

def parse_pdf_via_plumber(pdf_file):
  extracted_table = []
  with pdfplumber.open(pdf_file) as pdf:
        pages = pdf.pages
        for i,page in enumerate(pages):
            print("Parsing Page: " + str(i + 1) + " of " + str(len(pages)))
            #text = page.extract_text()
            #print(text)
            if i == 0:
                global po_box_text
                po_box_text = get_po_box(page)
                global sold_to_text 
                sold_to_text = get_sold_to(page)
            
            extracted_table.extend(get_line_items(page))
            #print(extracted_table)
            #did individual parsing of each column, code is moved to invoice-experiment.py

  return extracted_table         
            

def rotate_pdf(pdf_path):
    pdf_document = fitz.open(pdf_path)
    # Loop through each page in the document
    for page_num in range(pdf_document.page_count):
        print("Parsing Page: " + str(page_num + 1) + " of " + str(pdf_document.page_count))
        page = pdf_document.load_page(page_num)
        page.set_rotation(-90)
    pdf_document.save("input_pdf\\CCDIS-RCV7-029819_rotated.pdf")


def post_processing(extracted_data):
    df = pd.DataFrame(extracted_data)
    #hide not required columns
    df.drop(df.columns[[2,5,7]], axis=1, inplace=True)
    
    #hide rows in column where length is less than specific value
    df = df.drop(df[df[1].map(len) < 2].index)
    df = df.drop(df[df[4].map(len) < 2].index)
    df = df.drop(df[df[4].map(len) >= 7].index)

    #replace | sign with ''  and also remove non-numeric data from numeric columns
    df = df.apply(lambda x: x.str.strip().str.replace(r'\|', '', regex=True))
    df.loc[1:, 0] = df.loc[1:, 0].astype(str).str.replace(r'\D', '', regex=True)
    df.loc[1:, 1] = df.loc[1:, 1].astype(str).str.replace(r'\D', '', regex=True)
    df.loc[1:, 3] = df.loc[1:, 3].astype(str).str.replace(r'\D', '', regex=True)
    df[3] = df[3].astype(str).str.replace(';', '')
    
    print("Post processing of data completed")
    return df
    
def create_output_file(df):
    output_file_name = 'mancini_beverage_invoices_output.csv'
    with open(output_file_name, 'w') as file:
        text = """MANCINI C&C BEVERAGE """
        text += """\n"""
        text += '"' + po_box_text + '"'
        text += """\n"""
        text += sold_to_text
        file.write(text)

    df.to_csv(output_file_name, mode='a', header=True, index=True)
    print("Output file " + output_file_name + " created successfully")
    

# Path to your PDF file
#pdf_path = 'input_pdf\\CCDIS-RCV7-029819.pdf'
#rotate_pdf(pdf_path)    
pdf_path = 'input_pdf\\CCDIS-RCV7-029819_rotated.pdf'

extracted_data = parse_pdf_via_plumber(pdf_path)
df = post_processing(extracted_data)
create_output_file(df)

