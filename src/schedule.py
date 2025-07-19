import os

from src.gcp.gsheet import ClientTagSheet
from src.chat.line import LineApp
from src.settings import LINE_CHANNEL_ACCESS_TOKEN, LINE_CHANNEL_SECRET

FOLLOWUP_DELAY = 7

from datetime import datetime

def calculate_date_difference(start_date: str, end_date: str) -> int:
    """
    Calculate the number of days between two dates.

    Parameters:
    - start_date (str): The start date in 'YYYY-MM-DD' format.
    - end_date (str): The end date in 'YYYY-MM-DD' format.

    Returns:
    - int: Number of days between start_date and end_date.
    """
    date_format = "%Y-%m-%d"
    try:
        start = datetime.strptime(start_date, date_format)
        end = datetime.strptime(end_date, date_format)
        delta = end - start
        return delta.days
    
    except ValueError as e:
        print(f"Error parsing dates: {e}")
        return 0

def send_follow_up_message():
    """
    Send a follow-up message to the user.
    """
    line_app = LineApp(
        access_token=LINE_CHANNEL_ACCESS_TOKEN.replace('"', ''),
        channel_secret=LINE_CHANNEL_SECRET.replace('"', '')
    )
    print()

    # get all user
    client_tag_sheet = ClientTagSheet()
    sheet_df = client_tag_sheet.get_content_as_dataframe()

    # get
    calculate_diff_date = lambda date: calculate_date_difference(
        date, datetime.now().strftime('%Y-%m-%d')
    )
    sheet_df['need_follow_up'] = sheet_df['last message timestamp'].apply(calculate_diff_date)


    # filter user that need follow up
    users_to_follow_up = sheet_df[sheet_df['need_follow_up'] >= FOLLOWUP_DELAY]

    for _, row in users_to_follow_up.iterrows():
        user_id = row['user id']
        messages = f"Hello {row['profile_name']}, this is a follow-up message regarding your last contact with us. If you have any questions or need assistance, feel free to reach out!"
        
        # Send the follow-up message
        line_app.push_message(user_id, messages)


if __name__ == "__main__":
    send_follow_up_message()
    print("Follow-up messages sent successfully.")