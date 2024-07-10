# KNR Property Management 
- This generic script extracts information from all pdf provided by KNR property management. It extracts all the tabular data related to owner's statement and save the data in csv file. 
- Sample PDF "knr-property-owner-statement.pdf" is available in input_pdf folder
- output csv (knr_statement_output_data.csv) is also available

# Solution
- Find the table from input pdf
- Extract table headings with coordinates from PDF using PyMuPDF
- Read data row by row using PyMuPDF 
- Map the read text into corresponding table columns 
- Prepare the output csv file using pandas
 

# Language & Tools
- Python
- PyMuPDF (Fitz)
- Pandas
