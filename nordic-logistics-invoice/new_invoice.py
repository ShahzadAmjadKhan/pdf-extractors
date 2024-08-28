import pypdfium2 as pdfium


def process_file_via_pypdfium2(pdf_path):     
    pdf = pdfium.PdfDocument(pdf_path)     
    text = ""     
    for page_number in range(len(pdf)):         
        page = pdf.get_page(page_number)        
        page_text = page.get_textpage()         
        text += page_text.get_text_range()     
        # print(text)
        return text