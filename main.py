import asyncio
import time
import random
import pandas as pd
from simple_salesforce import Salesforce, SalesforceLogin
from datetime import datetime
import os
import traceback
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow

from config import Config

@dataclass
class Statistics:
    object_name: str
    start_time: datetime
    end_time: datetime
    duration: float
    last_refresh_date: str

class SalesforceClient:
    def __init__(self):
        self.sf: Optional[Salesforce] = None
        self.statistics: List[Statistics] = []

    def login(self) -> None:
        """Establish Salesforce connection with retry mechanism"""
        retries = 5
        for i in range(retries):
            try:
                session_id, instance = SalesforceLogin(
                    username=Config.SF_USERNAME,
                    password=Config.SF_PASSWORD,
                    security_token=Config.SF_TOKEN,
                    domain=Config.SF_DOMAIN
                )
                self.sf = Salesforce(instance=instance, session_id=session_id)
                print('Salesforce login successful!')
                return
            except Exception as e:
                wait_time = (2 ** i) + random.uniform(0, 1)
                print(f"Login attempt {i+1}/{retries} failed: {e}. Retrying in {wait_time:.2f} seconds...")
                time.sleep(wait_time)
        raise Exception("Max retries reached, Salesforce login failed.")

    def get_field_labels(self, object_name: str) -> Dict[str, str]:
        """Fetch field labels for an object"""
        field_label_map = {}
        soql_query = f"SELECT QualifiedApiName, Label, ValueTypeId FROM FieldDefinition WHERE EntityDefinition.QualifiedApiName = '{object_name}'"
        field_metadata = self.sf.query_all(soql_query)
        
        for field in field_metadata.get('records', []):
            qualified_name = field['QualifiedApiName']
            if qualified_name in Config.STANDARD_FIELDS or '__c' in qualified_name:
                field_label_map[qualified_name] = field['Label']
        
        return field_label_map

    def fetch_data(self, object_name: str, fields: List[str]) -> List[Dict[str, Any]]:
        """Fetch records for an object with retry mechanism"""
        soql_query = f"SELECT {', '.join(fields)} FROM {object_name}"
        print(f"Executing query: {soql_query}")
        
        retries = 5
        for i in range(retries):
            try:
                records = self.sf.query(soql_query)
                all_records = records.get('records', [])
                next_records_url = records.get('nextRecordsUrl')
                
                while not records.get('done'):
                    records = self.sf.query_more(next_records_url, identifier_is_url=True)
                    all_records.extend(records.get('records', []))
                    next_records_url = records.get('nextRecordsUrl')
                
                return all_records
            except Exception as e:
                wait_time = (2 ** i) + random.uniform(0, 1)
                print(f"Query attempt {i+1}/{retries} failed: {e}. Retrying in {wait_time:.2f} seconds...")
                time.sleep(wait_time)
        raise Exception(f"Max retries reached, query failed for {object_name}")

class GoogleDriveClient:
    def __init__(self):
        self.service = None
        self.folder_id = None

    def authenticate(self) -> None:
        """Authenticate with Google Drive"""
        creds = None
        if os.path.exists(Config.CREDENTIALS_FILE):
            creds = Credentials.from_authorized_user_file(Config.CREDENTIALS_FILE, Config.SCOPES)
        
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(Config.CREDENTIALS_FILE, Config.SCOPES)
                creds = flow.run_local_server(port=0)

            with open(Config.CREDENTIALS_FILE, 'w') as token:
                token.write(creds.to_json())

        self.service = build('drive', 'v3', credentials=creds)
        print('Google Drive authentication successful!')

    def get_or_create_folder(self) -> None:
        """Get or create the main folder in Google Drive"""
        query = f"name='{Config.DRIVE_FOLDER_NAME}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
        results = self.service.files().list(q=query, fields="files(id, name)").execute()
        folders = results.get('files', [])

        if folders:
            self.folder_id = folders[0]['id']
        else:
            folder_metadata = {
                'name': Config.DRIVE_FOLDER_NAME,
                'mimeType': 'application/vnd.google-apps.folder'
            }
            folder = self.service.files().create(body=folder_metadata, fields='id').execute()
            self.folder_id = folder['id']

    def upload_file(self, file_path: str) -> Dict[str, Any]:
        """Upload a file to Google Drive"""
        file_name = os.path.basename(file_path)
        start_time = datetime.now()
        log = {"Object Name": file_name, "Operation": "Upload Data", "Start Date Time": start_time}

        try:
            query = f"name='{file_name}' and '{self.folder_id}' in parents and trashed=false"
            results = self.service.files().list(q=query, fields="files(id)").execute()
            file_id = results['files'][0]['id'] if results['files'] else None

            media = MediaFileUpload(file_path, resumable=True)

            if file_id:
                self.service.files().update(fileId=file_id, media_body=media).execute()
            else:
                file_metadata = {'name': file_name, 'parents': [self.folder_id]}
                self.service.files().create(body=file_metadata, media_body=media).execute()

            end_time = datetime.now()
            log.update({
                "End Date Time": end_time,
                "Duration (seconds)": (end_time - start_time).total_seconds(),
                "Is Success": True,
                "Message": f"File '{file_name}' uploaded successfully.",
            })

        except Exception as e:
            end_time = datetime.now()
            log.update({
                "End Date Time": end_time,
                "Duration (seconds)": (end_time - start_time).total_seconds(),
                "Is Success": False,
                "Message": f"Error: {str(e)}\nTraceback: {traceback.format_exc()}",
            })

        return log

class DataPipeline:
    def __init__(self):
        self.sf_client = SalesforceClient()
        self.drive_client = GoogleDriveClient()
        self.logs: List[Dict[str, Any]] = []

    async def export_salesforce_object(self, object_name: str, writer: pd.ExcelWriter) -> None:
        """Process Salesforce object asynchronously"""
        start_time = datetime.now()
        print(f"\nProcessing object: {object_name}")
        print(f"Start Time: {start_time}")
        
        try:
            field_label_map = self.sf_client.get_field_labels(object_name)
            fields = list(field_label_map.keys())
            records = self.sf_client.fetch_data(object_name, fields)
            
            # Save records
            if records:
                fieldname_mapping = {v: k for k, v in field_label_map.items()}
                df = pd.DataFrame([
                    {field_label: record.get(field_api, '') 
                     for field_label, field_api in fieldname_mapping.items()}
                    for record in records
                ])
                
                if len(records) >= 1_000_000:
                    file_path = os.path.join(Config.LOCAL_FOLDER, f"{object_name}.csv")
                    df.to_csv(file_path, index=False)
                else:
                    sheet_name = object_name.replace("__c", "").replace("_", " ")
                    df.to_excel(writer, sheet_name=sheet_name, index=False)
                
                print(f"Data for {object_name} saved.")
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            self.sf_client.statistics.append(Statistics(
                object_name=object_name,
                start_time=start_time,
                end_time=end_time,
                duration=duration,
                last_refresh_date=datetime.today().strftime('%Y-%m-%d')
            ))
            
            print(f"End Time: {end_time}")
            print(f"Duration: {duration:.2f} seconds")
            
        except Exception as e:
            print(f"Error processing {object_name}: {str(e)}")
            traceback.print_exc()

    def save_statistics(self) -> None:
        """Save statistics to CSV file"""
        log_file = os.path.join(Config.LOCAL_FOLDER, Config.LOG_FILE_NAME)
        stats_data = [
            {
                "Object Name": stat.object_name,
                "Start Time": stat.start_time,
                "End Time": stat.end_time,
                "Duration (Seconds)": stat.duration,
                "Last Refresh Date": stat.last_refresh_date
            }
            for stat in self.sf_client.statistics
        ]
        
        if os.path.exists(log_file):
            existing_df = pd.read_csv(log_file)
            new_df = pd.DataFrame(stats_data)
            df = pd.concat([existing_df, new_df], ignore_index=True)
        else:
            df = pd.DataFrame(stats_data)
        
        df.to_csv(log_file, index=False)
        print(f"Statistics saved to {log_file}")

    async def run(self) -> None:
        """Main pipeline execution"""
        try:
            # Initialize
            Config.ensure_folders()
            
            # Salesforce Authentication and Export
            self.sf_client.login()
            excel_path = os.path.join(Config.LOCAL_FOLDER, "all_data.xlsx")
            async with pd.ExcelWriter(excel_path) as writer:
                await asyncio.gather(*(
                    self.export_salesforce_object(obj, writer)
                    for obj in Config.OBJECT_NAMES
                ))
            
            # Save Statistics
            self.save_statistics()
            
            # Google Drive Upload
            self.drive_client.authenticate()
            self.drive_client.get_or_create_folder()
            
            # Upload all files
            for filename in os.listdir(Config.LOCAL_FOLDER):
                if filename.endswith(('.xlsx', '.csv')):
                    file_path = os.path.join(Config.LOCAL_FOLDER, filename)
                    log = self.drive_client.upload_file(file_path)
                    self.logs.append(log)
            
            print("Pipeline completed successfully!")
            
        except Exception as e:
            print(f"Pipeline failed: {str(e)}")
            traceback.print_exc()

if __name__ == "__main__":
    pipeline = DataPipeline()
    asyncio.run(pipeline.run())
