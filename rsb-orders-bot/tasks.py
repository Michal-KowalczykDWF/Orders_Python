from robocorp.tasks import task
from robocorp import browser, http
from RPA.Tables import Tables
from RPA.PDF import PDF
from RPA.Archive import Archive


@task
def make_order():
    """Robot downloads .csv file with order data and places orders on rsb website, then saves them in PDF files"""
    # browser.configure(slowmo=200)
    orders = get_orders_input_data()
    navigate_to_orders_page()
    place_orders(orders)
    archive_receipts()


def get_orders_input_data():
    """Download orders data"""
    http.download(url="https://robotsparebinindustries.com/orders.csv", overwrite=True)
    orders_table = Tables()
    orders = orders_table.read_table_from_csv("orders.csv")
    return orders


def navigate_to_orders_page():
    """Navigates to orders page"""
    browser.goto(url="https://robotsparebinindustries.com/#/robot-order")

def click_popup():
    """Handle popup after openning the orders page"""
    page = browser.page()
    popup_visible = page.is_visible("//button[contains(text(),'OK')]")
    if popup_visible:
        page.click("//button[contains(text(),'OK')]")

def place_orders(orders):
    """For each order line fill in the form and save as PDF"""
    
    for row in orders:
        print(f"Order number: {row['Order number']}")
        click_popup()
        fill_order_form(row)



def fill_order_form(row):
    """Fill order form with input data"""
    page = browser.page()
    page.select_option("//select[@id='head']",row['Head'])
    page.click(f"//input[@id='id-body-{row['Body']}']")
    page.type("//input[@placeholder='Enter the part number for the legs']", row['Legs'])
    page.type("//input[@id='address']",row['Address'])
    page.click("//button[@id='preview']")
        
    receipt_visible = False
    try_counter = 1

    while not receipt_visible or try_counter < 3:
        
        try:
            page.click("//button[@id='order']")
        except:
            break

        receipt_visible = page.is_visible('.alert-success')
        if receipt_visible: break
        try_counter += 1
    
    if receipt_visible:
        receipt_pdf = save_order_as_pdf(row['Order number'])
        screenshot = get_robot_screenshot(row['Order number'])
        embed_screenshot_to_pdf(screenshot, receipt_pdf)
        page.click("//button[@id='order-another']")
    else:
        page.reload() #Failed to submit order, just reload page for the next order - normally would throw an exception


def save_order_as_pdf(order_number):
    """Save fulfilled order as a pdf file"""
    page = browser.page()
    receipt_html = page.locator('.alert-success').inner_html()
    pdf_path = f"output/receipts/receipt_{order_number}.pdf"
    pdf = PDF()
    pdf.html_to_pdf(receipt_html, pdf_path)
    return pdf_path

def get_robot_screenshot(order_number):
    """Save robot preview image"""
    page = browser.page()
    screenshot_path = f'output/screenshots/screenshot_{order_number}.jpg'
    preview_html = page.locator("//div[@id='robot-preview-image']")
    preview_html.screenshot(path=screenshot_path)
    return screenshot_path

def embed_screenshot_to_pdf(screenshot, pdf_file):
    """Add screenshot to the pdf file"""
    pdf = PDF()
    pdf.add_files_to_pdf(files=[screenshot], target_document=pdf_file, append=True)
    
def archive_receipts():
    """ZIP receipt files"""
    lib = Archive()
    lib.archive_folder_with_zip('output/receipts', 'receipts.zip')