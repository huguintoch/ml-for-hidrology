from __future__ import print_function

import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/drive.metadata.readonly']


def authenticate():
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
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
    return creds


def get_items_in_dir(service, folder_id):
    files = []
    page_token = None
    while True:
        response = service.files().list(q=f"parents = '{folder_id}'",
                                        fields='nextPageToken, '
                                               'files(id, name)',
                                        pageToken=page_token).execute()
        files.extend(response.get('files', []))
        page_token = response.get('nextPageToken', None)
        if page_token is None:
            break
    return files


def print_formatted_items(items):
    for item in items:
        print(u'{0} ({1})'.format(item['name'], item['id']))


def main():
    creds = authenticate()

    try:
        service = build('drive', 'v3', credentials=creds)

        # Get items in main dir
        root_dir_id = '1qu7sVR2KbApRgM6MURl73oVxzIfB5fsP'
        sub_dirs = get_items_in_dir(service, root_dir_id)
        total_items = 0

        # Get items in sub dir
        for sub_dir in sub_dirs:
            print('Listing items in {0}'.format(sub_dir['name']))
            sub_dir_items = get_items_in_dir(service, sub_dir['id'])
            sub_dir_len = len(sub_dir_items)
            total_items += sub_dir_len
            print(sub_dir_len)
            # print_formatted_items(sub_dir_items)

        print('Total items: {0}'.format(total_items))

    except HttpError as error:
        print(f'An error occurred: {error}')


if __name__ == '__main__':
    main()
