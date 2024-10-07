from pdf2image import convert_from_path
import glob
import pytesseract
from wand.image import Image
from PIL import Image as PILImage
import os


input_path = "input_pdf\\"
images_path = "images\\"
output_path = "output_pdf\\"
def get_images_from_pdf(pdf_name, start_page=0, end_page=1000):
    # Convert PDF to a list of images
    pages = convert_from_path(input_path + pdf_name, 400, first_page=start_page, last_page=end_page, grayscale=True)  # 300 DPI for better quality

    # Save each page as an image
    for page_num, image in enumerate(pages):
        image.save(f'{images_path}\\page_{page_num + 1}.png', 'PNG')

def deskew():
    for file in glob.glob(images_path + '*.png'):
        print(f'deskew: {file}')
        file_name = os.path.basename(file).split('.')[0]
        with Image(filename=file) as img:
            img2 = img.clone()
            img.crop(width=int(img.width/2))
            img2.crop(left=int(img2.width/2), right=img2.width)
            img.deskew(threshold=0.5)
            img.transform_colorspace('gray')
            img.contrast()
            # img.adaptive_threshold(width=2, height=2)
            img2.deskew(threshold=0.5)
            img.save(filename=f'{images_path}{file_name}_left_deskew.png')
            img2.save(filename=f'{images_path}{file_name}_right_deskew.png')

def ocr_image():
    for file in glob.glob(images_path + '*_deskew.png'):
        img = PILImage.open(file)
        file_name = os.path.basename(file).split('.')[0]
        file_name = os.path.join(images_path, file_name) + '.txt'
    #img = img.convert('L')  # Convert to grayscale
    #img = img.point(lambda x: 0 if x < 128 else 255, '1') # Optional: Enhance the image further if needed (e.g., binarization)
        custom_config = r'--oem 1 -l eng --psm 6'
        text = pytesseract.image_to_string(img, config=custom_config)
        with open(file_name, 'w') as f:
            f.write(text)
        print("Text: " + file_name + " created after ocr text extraction." )

get_images_from_pdf("resultsanddata2000.pdf",47,48)
deskew()
ocr_image()
