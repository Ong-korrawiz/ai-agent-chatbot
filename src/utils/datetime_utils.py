from datetime import datetime, date


def day_diff(input_date: str) -> int:
    """
    Calculate the difference in days between input date and today.
    
    Args:
        input_date: Date string (YYYY-MM-DD), date object, or datetime object
        
    Returns:
        int: Number of days difference (positive if input date is in future, 
             negative if in past, 0 if same day)
             
    Examples:
        >>> day_diff("2025-07-20")
        0  # if today is 2025-07-20
        
        >>> day_diff("2025-07-21") 
        1  # tomorrow
        
        >>> day_diff("2025-07-19")
        -1  # yesterday
    """
    today = date.today()
    
    # Handle different input types
    if isinstance(input_date, str):
        # Parse string date (YYYY-MM-DD format)
        target_date = datetime.strptime(input_date, "%Y-%m-%d").date()
    elif isinstance(input_date, datetime):
        # Extract date from datetime object
        target_date = input_date.date()
    elif isinstance(input_date, date):
        # Already a date object
        target_date = input_date
    else:
        raise TypeError("input_date must be a string (YYYY-MM-DD), date, or datetime object")
    
    # Calculate difference
    diff = (today - target_date).days
    return max(diff, 0)  # Ensure non-negative result