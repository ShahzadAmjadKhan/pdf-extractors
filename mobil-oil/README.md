# Mobil oil
- Extract information about the Car mobil oil available from PDF [mobil.pdf](./input_pdf/mobil.pdf) also available at [link](chrome-extension://efaidnbmnnnibpcajpcglclefindmkaj/https://content21.blob.core.windows.net/web-hosting/clients/mann-hummel/estore/catalogs/2023/2023%20Mobil1%20Oil%20Filter%20Catalog.pdf)
- Stores information for cars and mobil oil in CSV

# Solution
- Extract text from PDF using PyMuPDF
- Each page text is parsed to identify the required data for Car and mobil oil.
- Regular expression is used to determine different fields
- Following information is stored in CSV:
  - PAGE_NUMBER
  - MANUFACTURER
  - YEAR
  - MODEL
  - ENGINE
  - OIL

# Language & Tools
- Python
- PyMuPDF (Fitz)
- Pandas
