import fitz  # PyMuPDF
import pandas as pd
import re


def valid_line(line):
    if not (line == 'MANUFACTURER-MODEL-ENGINE' or \
            line == 'FABRICANT-MODELE-MOTEUR' or \
            line == 'FABRICANTE-MODELO-MOTOR' or \
            line == 'Oil' or \
            line == 'FILTERS FOR PASSENGER CARS AND LIGHT TRUCKS/ FILTRES POUR VOITURES PARTICULIERES ET' or \
            line == 'VEHICULES UTILITAIRES LEGERS/ FILTROS PARA AUTOMOVILES Y CAMIONES LIGEROS' or \
            line == 'Voir las page 2 pour une explication des renvois en bas de la page.' or \
            line == 'Consulte la página 2 para obtener una explicación de las nota en la parte inferior de la página' or \
            line == 'equipped with a Hengst filter housing cap, using AC-Delco # PF2257G. Synthetic Oil Application. Premium filter recommended.    568 Supplied aftermarket version GM O-ring #12577653' or \
            line == 'only fits 2004 and later Cadillac, Chevrolet, GMC V6 engines. Synthetic Oil Application. Premium Filter Recommended.   ' or \
            line.startswith('3 Availability limited to existing inventory.') or \
            line.startswith('1 25 PSI by-pass valve Oil Filter') or \
            line.startswith('threaded engine stud.') or \
            line.startswith('574 Models without engine oil cooler.') or \
            line.startswith('threads - Only use on VIN X - Sedan models') or \
            line.startswith('Recommended.') or \
            line.startswith('Filter recommended.') or \
            line.startswith('Premium Filter Recommended.') or \
            line.startswith('550 Synthetic Oil Application.') or \
            line.startswith('For vehicles where the filter housing cap has a center post.')):
        return True

    return False

def parse_lines(page_with_lines):
    """
    Parse the extracted lines and maintain context to build a structured data list.
    """
    data = []
    manufacturer = None
    year = None
    model = None
    engine = None
    oils = []
    valid = False
    for line_obj in page_with_lines:
        page_number = line_obj['page_number']
        lines = line_obj['lines']
        for index, line in enumerate(lines):
            line = line.strip()

            if valid and valid_line(line):
            # Check for manufacturer line (e.g., "ACURA")
                if re.match(r'^[A-Z ]{2,}$|([A-Z ]{2,})\W\(cont\'d\)', line) and \
                    re.match(r'^\d{4}$|(^\d{4})\W\(cont\'d\)$', lines[index + 1]):
                    if manufacturer and model and engine and oils:
                        # Save the current data before resetting
                        data.append([page_number, manufacturer, year, model, engine, list(set(oils))])

                    manufacturer = line.split(" ")[0]
                    model = None
                    engine = None
                    oils = []
                    continue

                # Check for year line (e.g., "2023")
                if re.match(r'^\d{4}$|(^\d{4})\W\(cont\'d\)$', line):
                    if manufacturer and model and engine and oils:
                        # Save the current data before resetting
                        data.append([page_number, manufacturer, year, model, engine, list(set(oils))])
                    year = line.split(" ")[0]
                    model = None
                    engine = None
                    oils = []
                    continue

                # Check for model line (e.g., "MDX")
                if manufacturer != 'SAAB':
                    if (re.match(r'^[A-Z0-9a-z\-\s\(\)]+$', line) and manufacturer and
                            not re.match(r'M1C*-\d+\w|F\d{5}|Pri\.\sF\d{5}|Sec\.\sL\/F|w\/\sOil\sCooler\sM1C*-\d+\w', line)):
                        if model and engine and oils:
                            # Save the current data before resetting
                            data.append([page_number, manufacturer, year, model, engine, list(set(oils))])
                        model = line
                        engine = None
                        oils = []
                        continue
                else:
                    if (re.match(r'^[A-Z0-9a-z\-\s\(\)\.]+$', line) and manufacturer and
                            not re.match(r'M1C*-\d+\w|F\d{5}|Pri\.\sF\d{5}|Sec\.\sL\/F|w\/\sOil\sCooler\sM1C*-\d+\w', line)):
                        if model and engine and oils:
                            # Save the current data before resetting
                            data.append([page_number, manufacturer, year, model, engine, list(set(oils))])
                        model = line
                        engine = None
                        oils = []
                        continue

                # Check for engine line
                if re.match(r'^[A-Za-z0-9\s\.\(\)\/\-\:\,]+$', line) and model:
                    line = line.replace(" ","")
                    if not re.match(r'M1C*-\d+\w|F\d{5}|Pri\.\sF\d{5}|Sec\.\sL\/F|w\/\sOil\sCooler\sM1C*-\d+\w', line):
                        if engine is not None and line != '(Electric/Gas)' and line != '(Electric/Gas) (Mexico)' and line != '(Electric/Gas) (Canada)':
                            data.append([page_number, manufacturer, year, model, engine, list(set(oils))])
                            oils = []
                        if line != '(Electric/Gas)' and line != '(Electric/Gas) (Mexico)' and line != '(Electric/Gas) (Canada)':
                            engine = line
                        else:
                            engine = engine + " " + line
                    else:
                        # Process oils related to the engine
                        oils.extend(re.findall(r'M1C*-\d+\w|F\d{5}|Pri\.\sF\d{5}|Sec\.\sL\/F|w\/\sOil\sCooler\sM1C*-\d+\w', line))
                    continue

            if line == "Oil":
                valid = True
                # Check for oil line
                # if re.match(r'^\s*M1C+-\d+[A-Z]*\s*\d*', line) and engine:
                #     oils.extend(re.findall(r'M1-\d+[A-Z]*\s*\d*', line))

    # Append the last processed entry if it exists
        if model and engine and oils:
            data.append([page_number, manufacturer, year, model, engine, list(set(oils))])

    return data

# Path to the PDF file
pdf_path = '.\input_pdf\mobil.pdf'  # Update this to your actual PDF path

# Open the PDF file
pdf_document = fitz.open(pdf_path)

# Initialize a list to store the text lines
all_lines = []
lines_with_page = []


def remove_duplicate_lines(text):
    lines = []
    page = False
    for line in text:
        if line == 'FILTERS FOR PASSENGER CARS AND LIGHT TRUCKS/ FILTRES POUR VOITURES PARTICULIERES ET' and not page:
            page = True

        if page:
            lines.append(line)

    return lines
# Extract text from each page
for page_number in range(len(pdf_document)):
    if page_number >= 6 and page_number <= 272:
        page = pdf_document.load_page(page_number)
        # blocks = page.get_text("dict", flags=11)["blocks"]
        text = page.get_text("text")
        all_lines.extend(text.split('\n'))
        all_lines = remove_duplicate_lines(all_lines)
        obj = {
            'page_number' : page_number,
            'lines': all_lines
        }
        lines_with_page.append(obj)
        all_lines = []

# Close the PDF file
pdf_document.close()

# Extract table data from the text lines
extracted_data = parse_lines(lines_with_page)

# Convert the extracted data into a DataFrame
df = pd.DataFrame(extracted_data, columns=["PAGE_NUMBER","MANUFACTURER", "YEAR", "MODEL", "ENGINE", "OIL"])

# Convert the OIL column to a string representation of a list
df["OIL"] = df["OIL"].apply(lambda x: str(x))

# Display the extracted table data
print("Extracted Table Data:")
print(df)

# Save the extracted table data to a CSV file
csv_path = '.\output\extracted_table.csv'
df.to_csv(csv_path, index=False)
print(f"Table data saved to {csv_path}")
