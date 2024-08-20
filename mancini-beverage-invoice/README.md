# Mancini C&C Beverage Invoice Data Extraction 
- This script use advanced OCR technique to extract information from invoices provided by Mancini C&C Beverage (https://ipn.paymentus.com/rotp/mnbv). It extracts customer information and all the line items available in invoice alongwith their description fields, cost etc. It then dumps all the information in csv file. 
- Provided PDF file cannot be directly read as it is made up of images. OCR is required to fetch data. As invoices concern tabular data, to preserve tabular data layout pytesseract and pdfplumber are used to complete it. 
- Tesseract, Pytesseract, PDFPlumber libraries are used for OCR, image creation, table marking on images and text extraction
- See below screenshot of invoice 


- see below screenshot of extracted data
  


# Solution
- Script first rotates the pdf file in right direction using pymupdf library.
- Script then identifies the areas need to be OCR. It creates images using BBOX. Pytesseract is then used to extract text. 
- LineItems are defined in tabular form so in order to preserve layout of line items PDFPlumber library is used to draw table on OCRed image pdf file. 
- Table is drawn by identifying the Text height and width. Column widths and row heights are calculated based character width and height, 
- Per invoice following attribues are read: Loc 	NUM.	CASES	SIZE	DESCRIPTION	PRICE	DISC.	PRICE	DEPOSIT TOTAL	TOTAL
- Pandas data frames are used for post processing of data which involves column hiding, unwanted text removal etc 
- It consolidates the information in a csv file (mancini_beverage_invoices_output.csv).
 

# Language & Tools
- Python
- tesseract
- pytesseract
- pdfplumber
- Pandas


