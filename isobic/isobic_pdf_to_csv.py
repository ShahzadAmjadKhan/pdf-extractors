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
    print("{}: Startiong download file: {}".format(datetime.datetime.now(), URL))
    response = requests.get(URL,timeout=120)
    if response.content:
        with open(PDF_FILE_PATH, 'wb') as f:
            f.write(response.content)
    else:
        print("{}: Unable to download file:".format(datetime.datetime.now()))

    print("{}: File download complete:".format(datetime.datetime.now(), URL))


def convert_pdf():

    file = open(PDF_FILE_PATH, 'rb')
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
        list_of_dfs = tabula.read_pdf(URL, pages=pages_to_read, lattice=True, format="CSV", pandas_options=col2str)
        result_df = pd.concat(list_of_dfs)
        result_df.to_csv(csv_file_name,quoting=csv.QUOTE_ALL)
        print("{}: File created: {}".format(datetime.datetime.now(), csv_file_name))
        last_page = last_page + READ_CHUNK
        if last_page > total_pages:
            last_page = total_pages

    file.close()


def merge_csvs():
    print ("{}: Merging CSVs".format(datetime.datetime.now()))
    csv_files = glob.glob(TEMP_FOLDER + '/*.{}'.format('csv'))

    df_csv_append = pd.concat(map(pd.read_csv, csv_files), ignore_index=True)
    df_csv_append.to_csv(os.path.join(OUTPUT_FOLDER, "ISOBIC.csv"), quoting=csv.QUOTE_ALL)
    print ("{}: CSVs Merged".format(datetime.datetime.now()))


def remove_directories():
    if os.path.isdir(TEMP_FOLDER):
        shutil.rmtree(TEMP_FOLDER)


if __name__ == "__main__":
    print("{}: Starting process to convert ISOBIC PDF from {} to CSV".format(datetime.datetime.now(), URL))
    warnings.filterwarnings("ignore")
    create_directories()
    download_pdf()
    convert_pdf()
    merge_csvs()
    remove_directories()
    print("{}: Process completed".format(datetime.datetime.now()))