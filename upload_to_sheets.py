#!/usr/bin/env python3

import os
import pandas as pd
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import pickle

SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

def get_google_sheets_credentials():
    creds = None
    # The file token.pickle stores the user's access and refresh tokens
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    
    # If there are no (valid) credentials available, let the user log in
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    
    return creds

def upload_to_sheets(csv_file='issue_summary.csv'):
    try:
        # Read the CSV file
        df = pd.read_csv(csv_file)
        
        # Get Google Sheets credentials
        creds = get_google_sheets_credentials()
        service = build('sheets', 'v4', credentials=creds)
        
        # Create a new spreadsheet
        spreadsheet = {
            'properties': {
                'title': 'Goose Issues Summary'
            }
        }
        spreadsheet = service.spreadsheets().create(body=spreadsheet,
                                                  fields='spreadsheetId').execute()
        spreadsheet_id = spreadsheet.get('spreadsheetId')
        
        # Convert DataFrame to values list
        values = [df.columns.values.tolist()]  # Headers
        values.extend(df.values.tolist())      # Data
        
        body = {
            'values': values
        }
        
        # Update the spreadsheet with the data
        result = service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range='A1',
            valueInputOption='RAW',
            body=body
        ).execute()
        
        # Get the spreadsheet URL
        spreadsheet_url = f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}"
        print(f"\nSpreadsheet created successfully!")
        print(f"URL: {spreadsheet_url}")
        
        return spreadsheet_url
        
    except HttpError as error:
        print(f"An error occurred: {error}")
        return None

if __name__ == "__main__":
    if not os.path.exists('credentials.json'):
        print("Error: credentials.json file not found!")
        print("Please follow these steps:")
        print("1. Go to https://console.cloud.google.com/")
        print("2. Create a new project or select an existing one")
        print("3. Enable the Google Sheets API")
        print("4. Create credentials (OAuth 2.0 Client ID)")
        print("5. Download the credentials and save as 'credentials.json' in this directory")
        exit(1)
    
    upload_to_sheets()