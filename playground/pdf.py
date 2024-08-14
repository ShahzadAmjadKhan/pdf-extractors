import fitz  # PyMuPDF

def extract_form_fields_with_page_numbers(pdf_path):
    # Open the PDF file
    document = fitz.open(pdf_path)

    for page_number in range(document.page_count):
        page = document[page_number]

        # Extract form fields on the page
        for field in page.widgets():
            field_name = field.field_name
            field_value = field.field_value
            field_type = field.field_type
            # Map field_type to a human-readable description
            # Map field_type to a human-readable description
            field_type_description = {
                0: "Text Field",
                1: "Check Box",
                2: "Radio Button",
                3: "List Box",
                4: "Drop-down List",
                5: "Button",
                7: "Text Area"
            }.get(field_type, "Unknown Type")

            print(f'Page {page_number + 1}: {field_name} = {field_value} of type: {field_type_description}')

    # Close the document
    document.close()

# Path to the PDF file
pdf_path = '../pdf-form-to-excel/input/UNIVIE_TCWB_HENIWI10.pdf'
extract_form_fields_with_page_numbers(pdf_path)
