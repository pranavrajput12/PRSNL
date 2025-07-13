from datetime import datetime, timedelta

import pytest

# Assuming your utility functions are in a module like 'app.utils.date_utils'
# For this test, we'll mock simple versions or assume they are directly available

# Mock utility functions for testing purposes if they don't exist yet
def format_date_for_display(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%d %H:%M:%S")

def is_today(dt: datetime) -> bool:
    return dt.date() == datetime.now().date()

def get_days_ago(dt: datetime) -> int:
    return (datetime.now().date() - dt.date()).days


def get_start_of_week(dt: datetime) -> datetime:
    return dt - timedelta(days=dt.weekday())

def get_start_of_month(dt: datetime) -> datetime:
    return dt.replace(day=1)


class TestDateUtils:

    def test_format_date_for_display(self):
        dt = datetime(2023, 1, 15, 10, 30, 45)
        assert format_date_for_display(dt) == "2023-01-15 10:30:45"

    def test_is_today(self):
        today = datetime.now()
        yesterday = today - timedelta(days=1)
        tomorrow = today + timedelta(days=1)
        
        assert is_today(today) == True
        assert is_today(yesterday) == False
        assert is_today(tomorrow) == False

    def test_get_days_ago(self):
        today = datetime.now()
        yesterday = today - timedelta(days=1)
        two_days_ago = today - timedelta(days=2)
        
        assert get_days_ago(today) == 0
        assert get_days_ago(yesterday) == 1
        assert get_days_ago(two_days_ago) == 2

    def test_get_start_of_week(self):
        # Monday
        dt = datetime(2023, 1, 16) # A Monday
        assert get_start_of_week(dt).date() == datetime(2023, 1, 16).date()
        
        # Wednesday
        dt = datetime(2023, 1, 18) # A Wednesday
        assert get_start_of_week(dt).date() == datetime(2023, 1, 16).date()
        
        # Sunday
        dt = datetime(2023, 1, 22) # A Sunday
        assert get_start_of_week(dt).date() == datetime(2023, 1, 16).date()

    def test_get_start_of_month(self):
        dt = datetime(2023, 3, 15)
        assert get_start_of_month(dt).date() == datetime(2023, 3, 1).date()
        
        dt = datetime(2023, 12, 31)
        assert get_start_of_month(dt).date() == datetime(2023, 12, 1).date()
