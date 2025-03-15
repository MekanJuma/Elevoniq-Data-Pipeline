from typing import List
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    # Salesforce Credentials
    SF_USERNAME: str = os.getenv('SF_USERNAME')
    SF_PASSWORD: str = os.getenv('SF_PASSWORD')
    SF_TOKEN: str = os.getenv('SF_TOKEN')
    SF_DOMAIN: str = os.getenv('SF_DOMAIN', 'login')

    # Google Drive Settings
    CREDENTIALS_FILE: str = 'credentials/google.json'
    SCOPES: List[str] = ['https://www.googleapis.com/auth/drive']
    DRIVE_FOLDER_NAME: str = os.getenv('GOOGLE_DRIVE_FOLDER_NAME', 'ELEVENIQ')

    # File Settings
    LOCAL_FOLDER: str = os.getenv('LOCAL_FOLDER', 'files')
    LOG_FILE_NAME: str = os.getenv('LOG_FILE_NAME', 'Pipeline_Logs.csv')

    # Salesforce Standard Fields
    STANDARD_FIELDS: List[str] = [
        "Id", "Name", "OwnerId", "CreatedDate", "LastModifiedDate", "CreatedById",
        "DeveloperName", "IsActive", "SobjectType",
        "BillingStreet", "BillingCity", "BillingPostalCode", "BillingCountry",
        "ShippingStreet", "ShippingCity", "ShippingPostalCode", "ShippingCountry",
        "Phone", "Email", "Salutation", "AccountId", "Title", "ContractId", "OrderId",
        "EndDate", "EffectiveDate", "ListPrice", "OrderItemNumber", "Product2Id", 
        "Quantity", "ServiceDate", "UnitPrice", "TotalPrice", "Status", "StageName",
        "ContractName", "OpportunityId", "OrderNumber", "Type", 
        "Pricebook2Id", "RecordTypeId", "StartDate", "ContractTerm", "ExternalId",
        "ProductCode", "Family", "IsStandard", "UseStandardPrice"
    ]

    # Salesforce Objects to Export
    OBJECT_NAMES: List[str] = [
        "RecordType", 
        "Account", 
        "Contact",
        "User",
        "Work_Order__c",
        "Elevator__c",
        "Property__c",
        "Property_Unit__c",
        "Elevator_Service_Cost__c",
        "Elevator_Document_Check__c",
        "Contract",
        "Opportunity",
        "Product2",
        "Pricebook2",
        "PricebookEntry",
        "OpportunityLineItem",
        "Order",
        "OrderItem",
        "OrderElevatorRelation__c",
        "Service_Fulfillment__c",
        "Elevator_Property__c",
        "OSI_WorkOrder_Item__c"
    ]

    @classmethod
    def ensure_folders(cls) -> None:
        """Ensure required folders exist"""
        os.makedirs(cls.LOCAL_FOLDER, exist_ok=True)
        os.makedirs(os.path.dirname(cls.CREDENTIALS_FILE), exist_ok=True) 