
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from pprint import pprint
from src.settings import GCP_CREDENTIALS
from src._types import ClientStatus, Platform

from pydantic import BaseModel

class ClientInfo(BaseModel):
    name: str
    email: str
    phone: str
    address: str
    notes: str


class Sheet:

    def __init__(self, spreadsheet_name: str, sheet_name: str):
        """
        Initialize the GoogleSheet client with credentials.
        """
        self.scope = ["https://spreadsheets.google.com/feeds",
                      'https://www.googleapis.com/auth/spreadsheets',
                      "https://www.googleapis.com/auth/drive.file",
                      "https://www.googleapis.com/auth/drive"]
        self.creds = ServiceAccountCredentials.from_json_keyfile_name(str(GCP_CREDENTIALS), self.scope)
        self.client = gspread.authorize(self.creds)

        self.speadsheet_name = spreadsheet_name
        self.sheet_name = sheet_name
        self.sheet = None

    def get_sheet(self):
        """
        Get the Google Sheet by name.
        """
        if self.sheet:
            return self.sheet

        try:
            spreadsheet = self.client.open(self.speadsheet_name)
            sheet = spreadsheet.worksheet(self.sheet_name)
            self.sheet = sheet
            return sheet
        except gspread.SpreadsheetNotFound:
            print(f"Spreadsheet '{self.speadsheet_name}' not found.")
            return None
        except gspread.WorksheetNotFound:
            print(f"Worksheet '{self.sheet_name}' not found in spreadsheet '{self.speadsheet_name}'.")
            return None
        
    def add_content(self, content: list[str]):
        """
        Add content to the Google Sheet at specified row and column.
        """
        sheet = self.get_sheet()
        sheet.append_row(content)

    def get_all_content(self) -> list[dict[str, any]]:
        """
        Get all content from the Google Sheet.
        """
        sheet = self.get_sheet()
        return sheet.get_all_records()
    
    def get_content_as_dataframe(self) -> pd.DataFrame:
        """
        Get content from the Google Sheet as a pandas DataFrame.
        """
        sheet = self.get_sheet()
        data = sheet.get_all_records()
        return pd.DataFrame(data)
    
    def get_column(self, col_id: int):
        sheet = self.get_sheet()

        return sheet.col_values(col_id)


class ClientTagSheet(Sheet):
    def __init__(self):
        super().__init__(
            spreadsheet_name="Client-detail-spread-sheet",
            sheet_name="Client tag"
        )
    
    def has_profle(self, profile_name: str) -> bool:
        recorded_profile = self.get_column(1)
        recorded_profile = set(recorded_profile)

        return profile_name in recorded_profile
        
    def add_new_profile(self, profile_name: str, user_id: str, platform: Platform) -> bool:
        today = pd.Timestamp.now().strftime('%Y-%m-%d')
        self.add_content(
                [
                    profile_name, 
                    ClientStatus.IN_PROGRESS, 
                    today, 
                    user_id,
                    platform
                ]
            )

    def update_timestamp(self, profile_name: str) -> bool:
        today = pd.Timestamp.now().strftime('%Y-%m-%d')
        sheet = self.get_sheet()
        cell = sheet.find(profile_name)

        # check if date cell is already updated
        if cell and sheet.cell(cell.row, 3).value == today:
            print(f"Timestamp for {profile_name} is already updated to {today}.")
            return False
        
        if cell and sheet.cell(cell.row, 2).value == ClientStatus.DONE:
            print(f"Profile {profile_name} is already marked as DONE. No need to update timestamp.")
            return False

        if cell:
            sheet.update_cell(cell.row, 3, today)
            return True
        return False
    
    def get_user_id(self, profile_name: str) -> str:
        sheet = self.get_sheet()
        cell = sheet.find(profile_name)
        if cell:
            return sheet.cell(cell.row, 4).value
        return None
        


if __name__ == "__main__":


    client_tag_sheet = Sheet(spreadsheet_name="Client-detail-spread-sheet", sheet_name="Client tag")
    sheet_content = client_tag_sheet.get_all_content()
    print("Sheet content:")
    print(sheet_content)
