
import pandas as pd
import gspread
import json
from oauth2client.service_account import ServiceAccountCredentials
from pprint import pprint
from src.settings import GOOGLE_API_CRED
from src._types import ClientStatus, Platform
from src.utils.common import ConfigUtils
from src.utils.datetime_utils import day_diff, get_thai_time
from datetime import time

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
        self.creds = ServiceAccountCredentials.from_json_keyfile_dict(json.loads(GOOGLE_API_CRED), self.scope)
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
        """
        Get user ID associated with a profile name.
        Args:
            profile_name (str): The name of the profile.
        Returns:
            str: User ID if found, None otherwise.
        """
        sheet = self.get_sheet()
        cell = sheet.find(profile_name)
        if cell:
            return sheet.cell(cell.row, 4).value
        return None


    def get_in_progress_profiles(self) -> list[dict[str, any]]:
        """
        Get all profiles with status IN_PROGRESS.

        Returns:
            list[dict[str, any]]: List of profiles with status IN_PROGRESS.
        """
        df = self.get_content_as_dataframe()
        in_progress_df = df[df['tag'] == ClientStatus.IN_PROGRESS]
        date_diff_thresh = ConfigSheet().get_follow_up_threshold()
        in_progress_df['date_diff'] = in_progress_df['last message timestamp'].apply(
            lambda x: day_diff(x) if isinstance(x, str) else day_diff(pd.Timestamp(x).strftime('%Y-%m-%d'))
        )
        in_progress_df_w_thresh = in_progress_df[in_progress_df['date_diff'] >= date_diff_thresh]
        in_progress_df_w_thresh = in_progress_df_w_thresh.reset_index(drop=True)
        return in_progress_df_w_thresh.to_dict(orient='records') 
    

class ConfigSheet(Sheet):
    def __init__(self):
        super().__init__(
            spreadsheet_name="Client-detail-spread-sheet",
            sheet_name="Config"
        )
        self.df = self.get_content_as_dataframe()
        self.transposed_df = self.df.T
        self.transposed_df.columns = self.transposed_df.iloc[0]
        self.transposed_df = self.transposed_df[1:]  # Remove the first row which is now the header
        print("Config Sheet Columns: ", self.transposed_df)

    def get_start_time(self) -> str:
        """
        """
        transposed_df = self.transposed_df
        start_time = transposed_df['start time'].values[0]
        return start_time
    
    def get_end_time(self) -> str:
        """
        """
        transposed_df = self.transposed_df
        end_time = transposed_df['end time'].values[0]
        return end_time
    

    def is_working_hour(self) -> bool:
        """
        Check if the current time is within working hours.

        Returns:
            bool: True if within working hours, False otherwise.
        """
        start_time_str = self.get_start_time()
        end_time_str = self.get_end_time()

        # Parse the time strings
        start_hour, start_minute = map(int, start_time_str.split(':'))
        end_hour, end_minute = map(int, end_time_str.split(':'))
        
        # Create time objects
        start_time = time(start_hour, start_minute)
        end_time = time(end_hour, end_minute)
        
        # Get current time
        current_time = get_thai_time()
        current_hour, current_minute = map(int, current_time.split(':'))
        current_time = time(current_hour, current_minute)
        
        # Handle overnight time ranges (e.g., 22:00 to 06:00)
        if start_time <= end_time:
            # Same day range (e.g., 09:00 to 17:00)
            return start_time <= current_time <= end_time
        else:
            # Overnight range (e.g., 22:00 to 06:00)
            return current_time >= start_time or current_time <= end_time
        


    def get_follow_up_threshold(self) -> int:
        """
        Get the follow-up threshold from the Config sheet.
        
        Returns:
            int: Follow-up threshold in days.
        """
        transposed_df = self.transposed_df
        follow_up_threshold = transposed_df.loc['follow up within (day)'].values[0]
        return int(follow_up_threshold)


    def get_follow_up_message(self) -> str:
        """
        Get the follow-up message from the Config sheet.
        
        Returns:
            str: Follow-up message.
        """
        transposed_df = self.transposed_df
        follow_up_message = transposed_df.loc['follow up message'].values[0]
        return follow_up_message


if __name__ == "__main__":


    # client_tag_sheet = Sheet(spreadsheet_name="Client-detail-spread-sheet", sheet_name="Client tag")
    # sheet_content = client_tag_sheet.get_all_content()
    # print("Sheet content:")
    # print(sheet_content)

    config_sheet = ConfigSheet()
    is_working_hour = config_sheet.is_working_hour()
    print(f"Is working hour: {is_working_hour}")