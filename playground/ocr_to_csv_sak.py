from multiprocessing import Value
import fitz  # PyMuPDF
import os
import pypdfium2 as pdfium
import pandas as pd
import tabula
import pdfplumber
import pytesseract
import camelot
from PIL import Image, ImageEnhance, ImageFilter
from pathlib import Path

# def draw_table_with_plumber(pdf_path, page):
#     extracted_table = []
#     with pdfplumber.open(pdf_path) as pdf:
#         pages = pdf.pages
#         explicit_horizontal_lines = [170, 190, 195, 215, 220, 240, 245, 265, 270, 290, 295, 315, 320, 340, 345, 365, 370, 390, 395, 415, 420, 440, 445, 465, 470, 490, 495, 515, 520, 540]
#         explicit_vertical_lines = []
#         for i,page in enumerate(pages):
#             text = page.extract_text(keep_blank_chars=True)
#             #print(text)
#             #     j = 1
#             #     coord =  7
#             #     explicit_horizontal_lines.append(coord)
#             #     coord = coord + 6
#             #     explicit_horizontal_lines.append(coord)
#             #     while j < 20:
#             #         coord = coord + 3.5 # 6 is charachter height, and 3.5 is distance between 2 vertical characters
#             #         explicit_horizontal_lines.append(coord)
#             #         coord = coord + 6
#             #         explicit_horizontal_lines.append(coord)
#             #         j = j + 1
#
#             #print(text)
#             explicit_vertical_lines = [50, 70, 150, 185, 220, 225, 250, 255, 280, 285, 310, 315, 340, 345, 370, 375, 400, 405, 430, 435, 460, 465, 495, 500, 540, 545, 585, 590, 635, 640, 665, 670, 695, 700   ] # for total  4 is character width,
#             table_settings = { "horizontal_strategy": "explicit", "vertical_strategy": "explicit",
#                                "explicit_horizontal_lines": explicit_horizontal_lines, "explicit_vertical_lines": explicit_vertical_lines, "snap_tolerance": 5}
#
#
#             im = page.to_image(500)
#             #imtable = im.reset().debug_tablefinder()
#             imtable = im.reset().debug_tablefinder(table_settings)
#             imtable.show()
#             table = page.extract_tables(table_settings)
#             for row in table:
#                 extracted_table = row
#                 print(row)
#     return extracted_table
#
# def ocr_image(image_name):
#     image_path = 'input_pdf\\' + image_name
#     img = Image.open(image_path)
#     custom_config = r'--oem 1 -l eng --psm 3'
#     text = pytesseract.image_to_string(img, config=custom_config)
#     print(f"{image_name} :\n{text}\n")
#     print("Image: " + image_name + " created for ocr text extraction." )
#     return text
#
# def create_image(page, image_name, image_bbox, _resolution):
#     image_path = 'input_pdf\\' + image_name
#     cropped_page = page.crop(image_bbox)
#     image_obj = cropped_page.to_image(resolution=_resolution)
#     image_obj.save(image_path)
#
#
#
# def get_table_items(page):
#     image_name = 'sample_page1.png'
#     my_file = Path("input_pdf\\sample_page1.png")
#     if not my_file.is_file():
#         # create file exists
#         image_bbox = (0, 0, page.width, page.height)
#         resolution = 500
#         create_image(page, image_name, image_bbox, resolution)
#         text = ocr_image(image_name)
#
#         #pdf = pytesseract.image_to_pdf_or_hocr('input_pdf\\line_items_unit_disc.png', extension='pdf')
#         pdf = pytesseract.image_to_pdf_or_hocr('input_pdf\\sample_page1.png', extension='pdf', config = " -c tessedit_create_pdf=1")
#         with open('input_pdf\\sample_page1.pdf', 'w+b') as f:
#             f.write(pdf) # pdf type is bytes by default
#     extracted_table = draw_table_with_plumber('input_pdf\\sample_page1.pdf', page)
#     print("Line items data extracted successfully." )
#     return extracted_table
#
# def parse_pdf_via_plumber(pdf_file):
#     extracted_table = []
#     with pdfplumber.open(pdf_file) as pdf:
#         pages = pdf.pages
#         for i,page in enumerate(pages):
#             print("Parsing Page: " + str(i + 1) + " of " + str(len(pages)))
#             #text = page.extract_text()
#             #print(text)
#             extracted_table.extend(get_table_items(page))
#             #print(extracted_table)
#             #did individual parsing of each column, code is moved to invoice-experiment.py
#
#     return extracted_table
#
#
# def rotate_pdf(pdf_path):
#     pdf_document = fitz.open(pdf_path)
#     file_name = os.path.basename(pdf_path)
#     # Loop through each page in the document
#     for page_num in range(pdf_document.page_count):
#         print("Parsing Page: " + str(page_num + 1) + " of " + str(pdf_document.page_count))
#         page = pdf_document.load_page(page_num)
#         page.set_rotation(90)
#     pdf_document.save(f"output_pdf\\{file_name}_rotated.pdf")
#
#
# def post_processing(extracted_data):
#     df = pd.DataFrame(extracted_data)
#
#     # Initialize an empty list to store the results
#     final_data = []
#
#     index_row = 1
#     # Loop over each row in the data
#     for row in extracted_data:
#         row.insert(0, 'SOUTH')
#         row.insert(1, 'KOLHAPUR')
#         row.insert(2, '201314\n201213')
#         row[3] = str(index_row)
#         index_row = index_row + 1
#
#         # Split each element in the row by '\n' (if any)
#         split_row = [entry.split('\n') for entry in row]
#
#         # Find the maximum number of splits (to handle rows with multiple splits)
#         max_splits = max(len(split) for split in split_row)
#
#         # For each row, create multiple rows if there are splits
#         for i in range(max_splits):
#             new_row = []
#             for entry in split_row:
#                 # If the current column has more than 1 split, use the appropriate split part
#                 # If the current column has no split, repeat the original value
#                 if len(entry) > i:
#                     new_row.append(entry[i])
#                 else:
#                     new_row.append(entry[0])  # Repeat the first value if no split
#             final_data.append(new_row)
#
#     add_headings(final_data)
#     # Convert the final data to a DataFrame
#     df = pd.DataFrame(final_data)
#
#     # Fill in missing values in the first column (name column)
#     df[0] = df[0].fillna(method='ffill')  # Forward fill missing values
#
#     # Save to CSV
#     df.to_csv('output-345.csv', index=False, header=False)
#
#     print("CSV file created successfully!")
#
#
#     print("Post processing of data completed")
#     return df
#
# def add_headings(extracted_data):
#     extracted_data.insert(0, ['Zone', 'District', "Year", "SL NO", 'FACTORY', 'START DATE', 'CLOSE DATE', 'GROSS DAYS', 'DUR DAYS', 'CANE SHORT', 'MECH + ELEC', 'PRO-CESS', 'CLEAN', 'MISC', 'TOTAL', 'INST. CAP (TCD)', 'CANE CRUSHED (M.T.)',
#                               'SUGAR PRODUCTION BAGGED', 'SUGAR PRODUCTION NET', 'RECOV % CANE', 'CAP UTLZ. %'])
#
# def create_output_file(df):
#     output_file_name = 'sample_original_output.csv'
#     #with open(output_file_name, 'w') as file:
#     #    text = """MANCINI C&C BEVERAGE """
#     #    text += """\n"""
#     #    #text += '"' + po_box_text + '"'
#     #    text += """\n"""
#     #    #text += sold_to_text
#     #    file.write(text)
#
#     df.to_csv(output_file_name, mode='a', header=True, index=True)
#     print("Output file " + output_file_name + " created successfully")

def get_data_using_camelot(pdf_path):
    output_file_name = "sample_output.csv"
    tables = camelot.read_pdf(pdf_path, flavor='stream')
    print(tables[0].df)
    tables[0].df.to_csv(output_file_name, mode='a', header=True,index=True)

def get_data_using_plumber(pdf_path):
    with pdfplumber.open(pdf_path) as pdf:
        page = pdf.pages[0]
        table = page.extract_text(layout=True)
        print(table)

def get_data_using_tabula(pdf_path):
    dfs = tabula.read_pdf(pdf_path, pages="1", stream=True, format="CSV")
    df = pd.concat(dfs)
    df.to_csv("output.csv")

def parse_file_via_pypdfium2(pdf_path):
    pdf = pdfium.PdfDocument(pdf_path)
    text = ""
    for page_number in range(len(pdf)):
        page = pdf.get_page(page_number)
        page_text = page.get_textpage()
        text = text + "\r\n" + page_text.get_text_range()

    print(text)

#from PIL import Image, ImageFilter


# Open an image
#image = Image.open('input_pdf\\sample_page1.png')

# Apply the sharpen filter
#sharpened_image = image.filter(ImageFilter.SHARPEN)

# Save the sharpened image
#sharpened_image.save('sharpened_image.png')

#from PIL import Image, ImageEnhance

# Open an image
#image = Image.open('image.png')

# Convert the image to RGB mode if it's in palette mode
#if image.mode == 'P':
#    image = image.convert('RGB')

# Create an enhancer object for sharpness
#enhancer = ImageEnhance.Sharpness(image)

# Increase sharpness (factor > 1 increases sharpness, factor < 1 decreases it)
#sharpened_image = enhancer.enhance(2.0)  # 2.0 is double the sharpness

# Save the sharpened image
#sharpened_image.save('sharpened_image.png')


# Path to your PDF file
pdf_path = '.\\output_pdf\\page_8.pdf'
# get_data_using_camelot(pdf_path)
# rotate_pdf(pdf_path)
# pdf_path = 'input_pdf\\Sample_Original_rotated_document.pdf'
#
extracted_data = parse_file_via_pypdfium2(pdf_path)
# df = post_processing(extracted_data)
# create_output_file(df)