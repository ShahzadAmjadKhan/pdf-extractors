# FFIEC Census Reports 
- This generic script extracts information from all 2023 FFIEC Census Report - Summary Census Demographic Information reports. Reports in PDF format can be accessed from url https://www.ffiec.gov/census/Default.aspx. 
- Sample PDF is available at [MSA_MD- 11244 - ANAHEIM-SANTA ANA-IRVINE, CA.pdf](input_pdf/MSA_MD- 11244 - ANAHEIM-SANTA ANA-IRVINE, CA.pdf)
- output csv is also available

# Solution
- Extract table headings with coordinates from PDF using PyMuPDF
- Read pdf block by block and read text and text coordinates from blocks 
- Map the read text into corresponding table columns using coordinates matching
- Prepare the output csv file using pandas
 

# Language & Tools
- Python
- PyMuPDF (Fitz)
- Pandas
