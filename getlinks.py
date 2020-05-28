from __future__ import print_function

import io
import pickle
import os.path
import re

from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# If modifying these scopes, delete the file token.pickle.
from googleapiclient.http import MediaIoBaseDownload

SCOPES = ['https://www.googleapis.com/auth/drive']
DES_PATH = os.getcwd() + "/"


def get_Gdrive_folder_id(drive, driveService, name, parent="root"):  # return ID of folder, create it if missing
    body = {'title': name,
            'mimeType': "application/vnd.google-apps.folder"
            }
    query = "title='Temp folder for script' and mimeType='application/vnd.google-apps.folder'" \
            " and '" + parent + "' in parents and trashed=false"
    if parent != "root":
        query += "and driveId='" + parent + "' and includeItemsFromAllDrives=true and supportsAllDrives = true"
    listFolders = drive.ListFile({'q': query})
    for subList in listFolders:
        if subList == []:  # if folder doesn't exist, create it
            folder = driveService.files().insert(body=body).execute()
            break
        else:
            folder = subList[0]  # if one folder with the correct name exist, pick it

    return folder['id']


def extract_file_ids_from_folder(drive, folderID):
    files = drive.ListFile({'q': "'" + folderID + "' in parents"}).GetList()
    fileIDs = []
    for file in files:
        fileIDs.append(file['id'])
    return fileIDs


def extract_files_id(links, drive):
    # copy of google drive file from google drive link :
    links = re.findall(r"\b(?:https?:\/\/)?(?:drive\.google\.com[-_&?=a-zA-Z\/\d]+)",
                       links)  # extract google drive links
    try:
        fileIDs = [re.search(r"(?<=/d/|id=|rs/).+?(?=/|$)", link)[0] for link in links]  # extract the fileIDs
        for fileID in fileIDs:
            if drive.auth.service.files().get(fileId=fileID).execute()[
                'mimeType'] == "application/vnd.google-apps.folder":
                fileIDs.extend(extract_file_ids_from_folder(drive, fileID))
                fileIDs.remove(fileID)
        return fileIDs
    except Exception as error:
        print("error : " + str(error))
        print("Link is probably invalid")
        print(links)


def copy_file(drive, fileId, parentFolder="root"):  # if different parentFolder, input the folder ID
    fileOriginMetaData = drive.auth.service.files().get(fileId=fileId).execute()
    """remove 4 last characters of the original file name 
    and add file extension(should be .rar) in case the file extension is missing from the name """
    nameNoExtension = ".".join(fileOriginMetaData['originalFilename'].split(".")[:-1])
    newFileName = nameNoExtension + "." + fileOriginMetaData['fileExtension']
    print("Name of the file on your google drive and on the disk: " + newFileName)
    folderID = get_Gdrive_folder_id(drive, drive.auth.service, "Temp folder for script", parentFolder)
    copiedFileMetaData = {"parents": [{"id": str(folderID)}], 'title': newFileName}  # ID of destination folder
    copiedFile = drive.auth.service.files().copy(
        fileId=fileId,
        body=copiedFileMetaData
    ).execute()
    return copiedFile


def delete_file(drive, id):
    drive.auth.service.files().delete(fileId=id).execute()

def getCreds():
    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
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

def getFileId(link,drive):
    id = link[33:]
    name =drive.files().get(fileId=id,fields='name').execute()
    return (id,name,'https://drive.google.com/uc?id='+id+'&export=download')

def main():
    """Shows basic usage of the Drive v3 API.
    Prints the names and ids of the first 10 files the user has access to.
    """
    # creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    # if os.path.exists('token.pickle'):
    #     with open('token.pickle', 'rb') as token:
    #         creds = pickle.load(token)
    # # If there are no (valid) credentials available, let the user log in.
    # if not creds or not creds.valid:
    #     if creds and creds.expired and creds.refresh_token:
    #         creds.refresh(Request())
    #     else:
    #         flow = InstalledAppFlow.from_client_secrets_file(
    #             'credentials.json', SCOPES)
    #         creds = flow.run_local_server(port=0)
    #     # Save the credentials for the next run
    #     with open('token.pickle', 'wb') as token:
    #         pickle.dump(creds, token)
    creds=getCreds()
    service = build('drive', 'v3', credentials=creds)

    # Call the Drive v3 API
    results = service.files().list(
        pageSize=2, fields="nextPageToken, files(id, name, webContentLink)").execute()
    items = results.get('files', [])

    if not items:
        print('No files found.')
    else:
        print('Files:')
        for item in items:
            try:
                print(u'{0} ({1}) ({2})'.format(item['name'], item['id'], item["webContentLink"]))
                fileId = item["id"]
                request = service.files().get_media(fileId=fileId)
                fPath = DES_PATH + item["name"]
                if os.path.exists(fPath):
                    print('file already exist ...')
                else:
                    fh = open(fPath, 'wb')
                    downloader = MediaIoBaseDownload(fh, request)
                    done = False
                    while done is False:
                        status, done = downloader.next_chunk()
                        print("downloading... ", int(status.progress()) * 100)
            except KeyError as k:
                print("no key found :", k)


if __name__ == '__main__':
    main()