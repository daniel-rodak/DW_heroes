from __future__ import print_function

import os.path
import pandas as pd
import numpy as np

import helpers as hp

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from config import *


def connect():
    """Shows basic usage of the Sheets API.
    Prints values from a sample spreadsheet.
    """
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if token_conf:
        creds = Credentials(**token_conf)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    try:
        return build('sheets', 'v4', credentials=creds)
    except HttpError as err:
        print(err)
        return

def update_values(spreadsheet_id, range_name, value_input_option,
                  _values):
    """
    Creates the batch_update the user has access to.
    Load pre-authorized user credentials from the environment.
    """
    try:

        service = connect()
        values = [
            [
                # Cell values ...
            ],
            # Additional rows ...
        ]
        body = {
            'values': _values
        }
        result = service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id, range=range_name,
            valueInputOption=value_input_option, body=body).execute()
        print(f"{result.get('updatedCells')} cells updated.")
        return result
    except HttpError as error:
        print(f"An error occurred: {error}")
        return error

def get_heroes():
    service = connect()
    sheet = service.spreadsheets()
    result = sheet.values().get(spreadsheetId=SPREADSHEET_ID,
                                range=REF_DESCS_RANGE_NAME).execute()
    values = result.get('values', [])
    ref_descs = pd.DataFrame(values[1:], columns=values[0]).set_index('Hero').drop(columns='Gdzie')
    heroes = {row[0]: hp.Hero(name=row[0], min_desc=row[1][1], opt_desc=row[1][2], whl_desc=row[1][3], priority=row[1][0]) for row in ref_descs.iterrows()}
    return heroes, ref_descs

def get_dw_descs(ref_descs):
    service = connect()
    sheet = service.spreadsheets()
    result = sheet.values().get(spreadsheetId=SPREADSHEET_ID,
                                range=DW_DESCS_RANGE_NAME).execute()
    values = result.get('values', [])
    dw_index = ref_descs.index
    dw_index.name = 'Nick'
    dw_descs = (
        pd.DataFrame(values[1:], columns=values[0], index=dw_index)
        .transpose()
        .replace(r"^\s*$", np.nan, regex=True)
        .fillna("-")
        .apply(lambda x: x.str.upper())
        .apply(lambda x: x.str.strip())
        .apply(lambda x: x.str.replace(r"\s\s+", " ", regex=True))
        .apply(lambda x: x.str.replace(r"^0.*", "-", regex=True))
        .apply(lambda x: x.str.replace(r"^[^ELMA].*", "-", regex=True))
    )
    return dw_descs

def get_status(heroes, dw_descs):
    stat_df=[]
    for hero in heroes.keys():
        stat_df.append(dw_descs[hero].str.strip().map(heroes[hero].get_status))
    return pd.DataFrame(stat_df)

def get_costs_frames(heroes, dw_descs):
    min_costs = hp.get_costs(dw_descs, heroes, cost_type = 'Minimum')
    opt_costs = hp.get_costs(dw_descs, heroes, cost_type = 'Optimum')
    return min_costs, opt_costs

def get_leaderboard(status_df, ref_descs):
    ret = (
        status_df
        .loc[ref_descs.loc[ref_descs['Priorytet'].astype(int)<4].index, :]
        .transpose()
        .assign(ile_dup=lambda df: df.apply(lambda x: np.sum(x=='Dupa'), axis=1))
        .assign(ile_min=lambda df: df.apply(lambda x: np.sum(x=='Minimum'), axis=1))
        .assign(ile_opt=lambda df: df.apply(lambda x: np.sum(x=='Optimum'), axis=1))
        .assign(ile_whl=lambda df: df.apply(lambda x: np.sum(x=='Whale'), axis=1))
        .iloc[:,-4:]
        .sort_values(['ile_dup', 'ile_min', 'ile_opt', 'ile_whl'])
    )
    return ret

def main():
    heroes, ref_descs = get_heroes()
    dw_descs = get_dw_descs(ref_descs)
    status_df = get_status(heroes, dw_descs)
    min_costs, opt_costs = get_costs_frames(heroes, dw_descs)
    leaderboard = get_leaderboard(status_df, ref_descs)

    update_values(SPREADSHEET_ID, DW_DESCS_WRITE_RANGE_NAME, "RAW", status_df.to_numpy().tolist())
    update_values(SPREADSHEET_ID, COSTS_MIN_WRITE_RANGE_NAME, "RAW", min_costs.to_numpy().tolist())
    update_values(SPREADSHEET_ID, COSTS_OPT_WRITE_RANGE_NAME, "RAW", opt_costs.iloc[:, 2:].to_numpy().tolist())
    update_values(SPREADSHEET_ID, LEADERBOARD_RANGE_NAME, "RAW", leaderboard.reset_index().to_numpy().tolist())


if __name__ == '__main__':
    main()
