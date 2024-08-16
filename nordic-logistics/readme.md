# Nordic Logistics Invoice Data Extraction 
- This generic script extracts information from invoices provided by Nordic Logistics Association. It extracts all the tabular data related to owner's statement and save the data in csv file. 
- PDF cannot be directly read as it is made up of images. 
- Script first creates the image from given PDF and then OCR the image using pytesseract to extract the information per page. 
- It then used Regular Expressions to retrieve required data i.e. Page, Invoice Num, Invoice Date, Order No., Ext. order no., Customer Number, Loading date, Delivery date, Vessel Name, Port of loading, Port of delivery, Total amount without VAT, Due Date, Tour No.
- It consolidates the information in a csv file (invoice_output_data.csv). 


# Solution
- Use pdfplumber to navigate the pages, and extract image from pdf using BBOX boundaries
- OCR the Image using pytesseract to extract the information per page. 
- Use regular expression to read the required data
- Map the read text into corresponding csv columns 
- Prepare the output csv file using pandas
 

# Language & Tools
- Python
- pdfplumber
- tesseract
- pytesseract
- Pandas


