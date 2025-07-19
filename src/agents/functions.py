from src.gcp.gsheet import Sheet


def add_contact_info(
        name: str="",
        email: str="", 
        phone: str="", 
        address: str="", 
        additional_requirements: str=""):
    """
    Add client contact information to the Google Sheet.
    """
    sheet = Sheet(spreadsheet_name="Client-detail-spread-sheet", sheet_name="Client info")
    content = [name, email, phone, address, additional_requirements]
    sheet.add_content(content)
    print(f"Added contact info: {content} to Google Sheet.")
    return "บันทึกข้อมูลสำเร็จ"


if __name__ == "__main__":
    # Example usage
    add_contact_info(
        name="Sam Doe",
        email="sam@gmail.com",
        phone="1234567890",
        address="123 Main St, Springfield",
        additional_requirements="No additional requirements"
    )