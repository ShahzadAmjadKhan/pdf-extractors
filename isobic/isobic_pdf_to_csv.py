import csv
import warnings
import os.path
import pandas as pd
import tabula
import glob
import datetime
import PyPDF2
import requests
import shutil



 
URL = "https://www.iso9362.org/bicservice/public/v1/bicdata/_pdf"
TEMP_FOLDER = "temp"
OUTPUT_FOLDER = "output"
PDF_FILE_NAME = "ISOBIC.pdf"
PDF_FILE_PATH = os.path.join(TEMP_FOLDER,PDF_FILE_NAME)
READ_CHUNK = 1000


def create_directories():
    if not os.path.isdir(TEMP_FOLDER):
        os.mkdir(TEMP_FOLDER)

    if not os.path.isdir(OUTPUT_FOLDER):
        os.mkdir(OUTPUT_FOLDER)


def download_pdf():
    print("{}: Starting download file: {}".format(datetime.datetime.now(), URL))
    request_headers = {
        "Accept-Language": "en-US,en;q=0.9",
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "Cookie": "ISO9362_COOKIE=2349340844.47873.0000",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36"
    }
    response = requests.get(URL,headers=request_headers, timeout=120)
    if response.content:
        with open(PDF_FILE_PATH, 'wb') as f:
            f.write(response.content)
    else:
        print("{}: Unable to download file:".format(datetime.datetime.now()))

    print("{}: File download complete:".format(datetime.datetime.now(), URL))


def convert_pdf():

    with open(PDF_FILE_PATH, 'rb') as file:
        pdf = PyPDF2.PdfReader(file)
        total_pages = len(pdf.pages)
        print("Total PDF Pages: {}".format(total_pages))

        first_page = 1
        last_page = READ_CHUNK

        for i in range(first_page, total_pages, READ_CHUNK):
            pages_to_read = str(i) + "-" + str(last_page)
            print("{} Reading PDF: {} ".format(datetime.datetime.now(), pages_to_read))
            csv_file_name = os.path.join(TEMP_FOLDER,"ISOBIC_" + str(i) + "-" + str(last_page) + ".csv")
            col2str = {'dtype': str}
            list_of_dfs = tabula.read_pdf(file, pages=pages_to_read, lattice=True, format="CSV", pandas_options=col2str)
            result_df = pd.concat(list_of_dfs)
            result_df.columns = result_df.columns.str.replace(r"[\r\n\t]", " ", regex=True)
            result_df.replace(to_replace=[r"\\t", r"\\n", r"\\r", "\t", "\n", "\r"], value=" ", regex=True, inplace=True)
            result_df.to_csv(csv_file_name,quoting=csv.QUOTE_ALL, index=False)
            print("{}: File created: {}".format(datetime.datetime.now(), csv_file_name))
            last_page = last_page + READ_CHUNK
            if last_page > total_pages:
                last_page = total_pages


def merge_csvs():
    print ("{}: Merging CSVs".format(datetime.datetime.now()))
    csv_files = glob.glob(TEMP_FOLDER + '/*.{}'.format('csv'))

    df_csv_append = pd.concat(map(pd.read_csv, csv_files), ignore_index=True)
    df_csv_append.to_csv(os.path.join(OUTPUT_FOLDER, "ISOBIC.csv"), quoting=csv.QUOTE_ALL, index=False)
    print ("{}: CSVs Merged".format(datetime.datetime.now()))


def remove_directories():
    if os.path.isdir(TEMP_FOLDER):
        shutil.rmtree(TEMP_FOLDER)


if __name__ == "__main__":
    print("{}: Starting process to convert ISOBIC PDF from {} to CSV".format(datetime.datetime.now(), URL))
    warnings.filterwarnings("ignore")
    # create_directories()
    # download_pdf()
    convert_pdf()
    merge_csvs()
    # remove_directories()
    print("{}: Process completed".format(datetime.datetime.now()))