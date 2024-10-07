import cv2
import pytesseract
from pdf2image import convert_from_path
import numpy as np
from PIL import Image
import pandas as pd


def correct_skew(image):
    # Convert to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)

    # Apply edge detection
    edges = cv2.Canny(gray, 50, 150, apertureSize=3)

    # Detect lines using Hough Transform
    lines = cv2.HoughLines(edges, 1, np.pi / 180, threshold=200)

    if lines is not None:
        # Calculate the angles of the lines
        angles = []
        for rho, theta in lines[:, 0]:
            angle = (theta * 180 / np.pi) - 90  # Convert radians to degrees
            angles.append(angle)

        # Compute the median angle
        median_angle = np.median(angles)

        # Rotate the image to correct skew
        (h, w) = image.shape[:2]
        center = (w // 2, h // 2)
        M = cv2.getRotationMatrix2D(center, median_angle, 1.0)
        corrected_image = cv2.warpAffine(image, M, (w, h), flags=cv2.INTER_CUBIC)

        return corrected_image

images = convert_from_path('.\\output_pdf\\Table1_Technical_201819_rotated.pdf')
processed_images = []
num_pages_to_process = min(20, len(images))
# Iterate over each page/image
for page_num in range(num_pages_to_process):

    image = images[page_num]
    # Convert PIL Image to NumPy array
    img_array = np.array(image)

    # Correct skew in the image
    # corrected_image = correct_skew(img_array)

    # Convert RGB to Grayscale (Optional, but improves OCR accuracy)
    gray_image = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)

    # Noise removal using GaussianBlur
    blurred_image = cv2.GaussianBlur(gray_image, (5, 5), 0)

    # # Apply thresholding to increase contrast
    # _, thresholded_image = cv2.threshold(blurred_image, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    # Resize the image to enhance resolution (e.g., double the size)
    height, width = blurred_image.shape
    new_width = int(width * 2)   # Double the width
    new_height = int(height * 2)  # Double the height
    resized_image = cv2.resize(blurred_image, (new_width, new_height), interpolation=cv2.INTER_CUBIC)

    # Sharpen the image using a kernel
    kernel = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]])
    sharpened_image = cv2.filter2D(resized_image, -1, kernel)

    # Save the grayscale image (optional step)
    output_image_filename = f'.\\output_pdf\\page_{page_num}_gray.png'
    cv2.imwrite(output_image_filename, sharpened_image, [cv2.IMWRITE_PNG_COMPRESSION, 0])

    # Perform OCR on the grayscale image
    pdf = pytesseract.image_to_pdf_or_hocr(sharpened_image, extension='pdf', config = " -c tessedit_create_pdf=1")
    with open(f'output_pdf\\page_{page_num}.pdf', 'w+b') as f:
        f.write(pdf) # pdf type is bytes by default

    special_config = '--psm 12 --oem 1'
    languages_ = "eng" # For multiple language use like "eng+rus+swe" and so on

    # data = pytesseract.image_to_data(
    #     sharpened_image,
    #     lang=languages_,
    #     output_type='string')
    #
    # # data_imp_sort = optimizeDf(data)
    # print(data)

    # text = pytesseract.image_to_string(sharpened_image)
    #
    # output_text_filename = f'.\\output_pdf\\page_{page_num}_text.txt'
    # with open(output_text_filename, 'w', encoding='utf-8') as text_file:
    #     text_file.write(text)
    #
    # print(f"Text from page {page_num} saved to {output_text_filename}")

    # Append the processed image to the list for PDF creation
    processed_images.append(Image.open(output_image_filename))

# Create a new PDF from the processed images
pdf_filename = '.\\output_pdf\\processed_output.pdf'
processed_images[0].save(pdf_filename, save_all=True, append_images=processed_images[1:])

print(f"PDF saved as: {pdf_filename}")

