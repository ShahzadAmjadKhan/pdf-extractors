# ISOBIC
- Extract information about the ISOBICs available from PDF https://www.iso9362.org/bicservice/public/v1/bicdata/_pdf
- Stores information in CSV format

# Solution
- Download the PDF file from URL in temp directory
- Determine total pages using PyPDF2
- Read table using tabula lib from each page of PDF
- Write data in CSV for each 1000 page [this is done to avoid memory issue]
- Merge CSVs into one

# Language & Tools
- Python
- PyPDF2
- Pandas
- tabula
