import os
import requests
from flask import Flask, request, send_file, render_template_string
from reportlab.lib.pagesizes import A6, landscape
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
import qrcode
from PIL import Image
from io import BytesIO
from datetime import datetime
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import Paragraph, Frame
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.lib.utils import ImageReader
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging


# Setup logging for debugging
logging.basicConfig(level=logging.DEBUG)

# Load environment variables from a .env file
load_dotenv()

# ERPNext API configuration from environment variables
ERP_URL = os.getenv("ERP_URL")
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")

app = Flask(__name__)

def get_item_details(item_code):
    url = f"{ERP_URL}/api/resource/Item/{item_code}"
    headers = {
        "Authorization": f"token {API_KEY}:{API_SECRET}"
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()["data"]

def create_qr_code(data, size):
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill='black', back_color='white').convert('RGB')
    # Ensure high resolution
    img = img.resize((size, size), Image.NEAREST)
    return img

def download_image(image_url):
    if image_url.startswith("/"):
        image_url = ERP_URL + image_url
    try:
        response = requests.get(image_url, stream=True)
        response.raise_for_status()
        return Image.open(BytesIO(response.content))
    except requests.exceptions.RequestException:
        return Image.open("./default.png")  # Return a default image if the image_url is not valid

def draw_text_center(pdf_canvas, text, x, y, width, height):
    styles = getSampleStyleSheet()
    style = styles["Normal"]
    style.alignment = TA_CENTER
    style.fontName = 'Helvetica-Bold'  # Set font to bold
    style.fontSize = 24 # Starting font size
    style.leading = style.fontSize + 2  # Add extra space between lines

    # Convert width and height to points (1 mm = 2.83465 points)
    available_width = width
    available_height = height


    # Create a paragraph and try to fit it in the available space
    while True:
        p = Paragraph(text, style)
        width_needed, height_needed = p.wrap(available_width, available_height)
    
        
        if height_needed <= available_height or style.fontSize <= 4:
            break
        
        # Reduce font size and try again
        style.fontSize -= 1
        style.leading = style.fontSize + 2  # Adjust leading accordingly

    # Check if the paragraph fits in the available space after adjusting font size
    

    p = Paragraph(text, style)
    width_needed, height_needed = p.wrap(available_width, available_height)

    # Draw the frame with a visible boundary for debugging
    frame = Frame(x, y, available_width, available_height, showBoundary=0, leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
    frame.addFromList([p], pdf_canvas)

def draw_text_left(pdf_canvas, text, x, y, width, height):
    styles = getSampleStyleSheet()
    style = styles["Normal"]
    style.alignment = TA_LEFT
    style.fontName = 'Helvetica'
    style.fontSize = 12  # Starting font size
    style.leading = style.fontSize + 2  # Add extra space between lines

    p = Paragraph(text, style)
    available_width, available_height = width, height

    while True:
        p = Paragraph(text, style)
        width_needed, height_needed = p.wrap(available_width, available_height)
        if height_needed <= available_height or style.fontSize <= 4:
            break
        style.fontSize -= 1

    frame = Frame(x, y, width, height, showBoundary=1, leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
    frame.addFromList([p], pdf_canvas)


def create_kanban_card_front(pdf_canvas, card_title, image, item_code, orderpage_link, default_supplier, supplier_part_no, x, y):
    card_width, card_height = landscape(A6)

    # Draw center line
    pdf_canvas.setStrokeColorRGB(0.8, 0.8, 0.8)  # Set grey color
    pdf_canvas.setLineWidth(1)
    line_x = x + (card_width) / 2  # Center of the card
    pdf_canvas.line(line_x, y, line_x, y + card_height)

    # Draw card title
    draw_text_center(pdf_canvas, card_title, 2 * mm, 83 * mm, 70 * mm, 20 * mm)

    # Draw item code
    pdf_canvas.setFont("Helvetica", 12)
    pdf_canvas.drawString(x + 4 * mm, y + card_height - 26 * mm, f"Item Code: {item_code}")

    # Draw Image
    image_reader = ImageReader(image)
    pdf_canvas.drawImage(image_reader, 7 * mm, 12 * mm, 60 * mm, 60 * mm)

    # Draw supplier text
    draw_text_left(pdf_canvas, f"Lieferant: {default_supplier}", 76 * mm, 90 * mm, 70 * mm, 12 * mm)

    # Draw supplier part number
    draw_text_left(pdf_canvas, f"L-Teilenummer: {supplier_part_no}", 76 * mm, 82 * mm, 70 * mm, 12 * mm)

    # Draw last price label
    draw_text_left(pdf_canvas, "Bestellmenge:", 76 * mm, 74 * mm, 70 * mm, 12 * mm)

    # Draw date and quantity label
    draw_text_left(pdf_canvas, "Kanban VE:", 76 * mm, 66 * mm, 70 * mm, 12 * mm)

    # Draw date and quantity label
    draw_text_left(pdf_canvas, "Letzer Preis:", 76 * mm, 58 * mm, 70 * mm, 12 * mm)

    # Draw date and quantity label
    draw_text_left(pdf_canvas, "Datum   -   Stk.", 76 * mm, 50 * mm, 70 * mm, 12 * mm)

     # Draw QR Code for order page or orderpage_link text
    if orderpage_link.startswith("http"):
        qr_size = 300  # Use higher resolution size
        qr_img = create_qr_code(orderpage_link, qr_size)
        qr_reader = ImageReader(qr_img)
        pdf_canvas.drawImage(qr_reader, (74 + 37 - 15) * mm, y + 6 * mm, 30 * mm, 30 * mm)
    else:
        draw_text_left(pdf_canvas, orderpage_link, 76 * mm, 25 * mm, 70 * mm, 12 * mm)

    # Draw QR Code for item_code
    qr_small_size = 150  # Use higher resolution size
    qr_small_img = create_qr_code(item_code, qr_small_size)
    qr_small_reader = ImageReader(qr_small_img)
    pdf_canvas.drawImage(qr_small_reader, x + 2 * mm, y + 2 * mm, 15 * mm, 15 * mm)

def process_item(item_code):
    try:
        item_details = get_item_details(item_code)
        title = item_details["item_name"]
        image_url = item_details.get("image", "./default.png")
        orderpage_link = item_details.get("orderpage_link", "")
        supplier = "Unknown Supplier"
        supplier_part_no = "Unknown Part No"
        if item_details.get("supplier_items"):
            supplier = item_details["supplier_items"][0]["supplier"]
            supplier_part_no = item_details["supplier_items"][0]["supplier_part_no"]

        if image_url.startswith("/"):
            image_url = ERP_URL + image_url

        image = download_image(image_url)

        return {
            "title": title,
            "image": image,
            "item_code": item_code,
            "orderpage_link": orderpage_link,
            "supplier": supplier,
            "supplier_part_no": supplier_part_no
        }
    except Exception as e:
        print(f"Fehler bei der Verarbeitung von Artikelnummer {item_code}: {e}")
        return None

def generate_kanban_pdf(item_codes):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"kanban_cards_{timestamp}.pdf"
    c = canvas.Canvas(filename, pagesize=landscape(A6))
    width, height = landscape(A6)

    # Use ThreadPoolExecutor for parallel processing
    with ThreadPoolExecutor(max_workers=10) as executor:
        future_to_item = {executor.submit(process_item, item_code): item_code for item_code in item_codes}
        for future in as_completed(future_to_item):
            item_data = future.result()
            if item_data:
                create_kanban_card_front(
                    c, 
                    item_data["title"], 
                    item_data["image"], 
                    item_data["item_code"], 
                    item_data["orderpage_link"], 
                    item_data["supplier"], 
                    item_data["supplier_part_no"],  # Pass supplier part number
                    0 * mm, 0 * mm
                )
                c.showPage()  # Go to the next page

    c.save()
    return filename

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        item_codes_input = request.form["item_codes"]
        item_codes = item_codes_input.split(',')
        item_codes = [code.strip() for code in item_codes]  # Remove any surrounding whitespace
        pdf_filename = generate_kanban_pdf(item_codes)
        return send_file(pdf_filename, as_attachment=True)

    html = """
    <form method="post">
        <label for="item_codes">Teilenummern (kommagetrennt):</label>
        <input type="text" id="item_codes" name="item_codes">
        <input type="submit" value="Generate KANBAN PDF">
    </form>
    """
    return render_template_string(html)

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0')
