import json
import os

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

# The ID and range of a sample spreadsheet.
SPREADSHEET_ID = os.environ.get('SPREADSHEET_ID')
REF_DESCS_RANGE_NAME = 'AE_S8_Raw!A1:F50'
DW_DESCS_RANGE_NAME = 'AE_S8_Raw!G1:BX50'
DW_DESCS_WRITE_RANGE_NAME = 'AE_S8!G2:BX50'
COSTS_MIN_WRITE_RANGE_NAME = 'AE_Koszty!A3:H282'
COSTS_OPT_WRITE_RANGE_NAME = 'AE_Koszty!I3:N282'
LEADERBOARD_RANGE_NAME = 'Ranking_dup!A2:E71'

token_conf = {
    "token": os.environ.get("TOKEN"),
    "refresh_token": os.environ.get("REFRESH_TOKEN"),
    "token_uri": "https://oauth2.googleapis.com/token", 
    "client_id": os.environ.get("CLIENT_ID"),
    "client_secret": os.environ.get("CLIENT_SECRET"),
    "scopes": ["https://www.googleapis.com/auth/spreadsheets"],
    # "expiry": "2022-10-14T07:16:29.384734Z",
}

