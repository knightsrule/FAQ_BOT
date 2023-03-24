
import os
from urllib.parse import urlparse
from config_parser import parse_config
import os
from io import BytesIO
import subprocess
from reportlab.pdfgen import canvas
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from PyPDF2 import PdfFileReader, PdfFileWriter, PdfReader, PdfWriter
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

def convert_to_pdf(input_file_path, output_file_path):

    print (input_file_path, output_file_path)
    srcFile = os.path.abspath(input_file_path)
    destFile = os.path.abspath(output_file_path)

    # set up the lp command to print to a PDF file using the cups-pdf driver
    lp_command = ['lp', '-d', 'PDF', '-o', 'OutputFile=' + destFile, srcFile]

    # call the lp command to print the input file to a PDF file
    subprocess.run(lp_command)

def text_to_fpdf(input_path, output_path):

    print(input_path, output_path)

    # save FPDF() class into # a variable pdf
    pdf = FPDF()  
  
    # Add a page
    pdf.add_page()
  
    # set style and size of font
    # that you want in the pdf
    pdf.add_font('Arial', '', 'arial.ttf', uni=True)  # added line
    pdf.set_font("Arial", size = 15)
 
    # open the text file in read mode
    f = open(input_path, "r")
 
    # insert the texts in pdf
    for i, x in enumerate(f):
        pdf.cell(200, 10, txt = x, ln = i, align = 'C')
  
    # save the pdf with name .pdf
    pdf.output(output_path) 

def text_to_pdf(input_path, output_path):
    # read the text file line by line
    with open(input_path, 'r') as f:
        lines = f.readlines()

    # create a new PDF file
    packet = BytesIO()
    can = canvas.Canvas(packet, pagesize=letter)

    # set the font and font size
    pdfmetrics.registerFont(TTFont('Arial', '/System/Library/Fonts/Supplemental/Arial.ttf'))
    can.setFont("Arial", 12)

    # set the starting position for the text
    x = 10
    y = 800

    # write each line of text to the PDF
    for line in lines:
        # check if the line is too long
        if pdfmetrics.stringWidth(line.strip(), 'Arial', 12) > letter[0] - 20:
            # split the line into words
            words = line.strip().split()
            # create a new line with the first word
            new_line = words[0]
            # add the remaining words to the line until it is too long
            for word in words[1:]:
                if pdfmetrics.stringWidth(new_line + ' ' + word, 'Arial', 12) < letter[0] - 20:
                    new_line += ' ' + word
                else:
                    can.drawString(x, y, new_line)
                    y -= 20
                    if y < 50:
                        can.showPage()
                        y = 800

                    new_line = word
            # write the last line
            can.drawString(x, y, new_line)
            y -= 20
        else:
            can.drawString(x, y, line.strip())
            y -= 20
            if y < 50:
                can.showPage()
                y = 800
                
    can.save()
    packet.seek(0)
    new_pdf = PdfReader(packet)

    # add the new PDF file to the output file
    output_pdf = PdfWriter()
    for page in new_pdf.pages:
        output_pdf.add_page(page)

    # save the output file
    with open(output_path, "wb") as outputStream:
        output_pdf.write(outputStream)

    print("File converted successfully.")

start_url, depth, log_level, secPDFURL, ifSaveHTML = parse_config()

# Parse the URL and get the domain
BASE_URL_DETAILS = urlparse(start_url)
BASE_DIRECTORY =  "text/"+ BASE_URL_DETAILS.netloc+"/"

if not os.path.exists(BASE_DIRECTORY + "pdf/"):
    os.mkdir(BASE_DIRECTORY + "pdf/")


# Get all the text files in the text directory
index = 0
for file in os.listdir(BASE_DIRECTORY + "txt/"):

    file_info = list(os.path.splitext(file))
    if file_info[1] and file_info[1] == ".txt":
        #print(file, file_info)
        text_to_pdf(BASE_DIRECTORY + "txt/" + file, BASE_DIRECTORY + "pdf/" + file_info[0] + '.pdf')
        #text_to_fpdf(BASE_DIRECTORY + "txt/" + file, BASE_DIRECTORY + "pdf/" + file_info[0] + '.pdf')
        #convert_to_pdf("./" + BASE_DIRECTORY + "txt/" + file, "./" + BASE_DIRECTORY + "pdf/" + file_info[0] + '.pdf')
    else:
        print("not a text file")