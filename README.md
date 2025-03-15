# Elevoniq Data Pipeline 🚀

An automated data pipeline that synchronizes data between Salesforce and Google Drive, built with Python using modern async programming and OOP principles.

## 🌟 Features

- **Salesforce Integration**
  - Automated data extraction from multiple Salesforce objects
  - Smart field mapping with label preservation
  - Retry mechanism for reliable data fetching
  - Handles large datasets (>1M records) efficiently

- **Google Drive Integration**
  - Automatic folder management
  - Smart file versioning (update existing files)
  - Secure authentication handling

- **Data Processing**
  - Asynchronous data processing for improved performance
  - Intelligent format selection (Excel/CSV) based on data size
  - Comprehensive error handling and logging

- **Statistics & Monitoring**
  - Detailed execution statistics
  - Performance metrics tracking
  - Operation logs with timestamps

## 🛠 Tech Stack

- Python 3.8+
- `simple-salesforce` for Salesforce API integration
- `pandas` for data manipulation
- `google-api-python-client` for Google Drive integration
- `python-dotenv` for environment management
- `aiohttp` for async operations

## 📦 Installation

1. Clone the repository:
```bash
git clone https://github.com/MekanJuma/Elevoniq-Data-Pipeline.git
cd Elevoniq-Data-Pipeline
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
   - Copy `.env.example` to `.env`
   - Fill in your credentials:
     - Salesforce credentials
     - Google Drive settings
     - Folder configurations

4. Ensure Google Drive credentials are in place:
```bash
mkdir -p credentials
# Place your google.json in credentials/
```

## 🚀 Usage

Run the pipeline:
```bash
python main.py
```

The pipeline will:
1. Connect to Salesforce
2. Extract data from configured objects
3. Save data locally
4. Upload to Google Drive
5. Generate statistics and logs

## 🏗 Project Structure

```
Elevoniq-Data-Pipeline/
├── main.py              # Main pipeline implementation
├── config.py            # Configuration and constants
├── requirements.txt     # Project dependencies
├── .env                 # Environment variables
├── credentials/         # API credentials
│   └── google.json     # Google Drive credentials
└── files/              # Data output directory
    ├── all_data.xlsx   # Combined data
    └── Pipeline_Logs.csv # Operation logs
```

## ⚙️ Configuration

### Salesforce Objects
Configure objects to sync in `config.py`:
```python
OBJECT_NAMES = [
    "Account",
    "Contact",
    "User",
    # Add more objects...
]
```

### Field Mappings
Standard fields are defined in `config.py`. Custom fields are automatically detected with the `__c` suffix.

## 🔄 Pipeline Flow

1. **Initialization**
   - Load configuration
   - Create necessary directories

2. **Salesforce Operations**
   - Authenticate
   - Extract data from configured objects
   - Process and transform data

3. **Local Storage**
   - Save data in appropriate formats
   - Generate statistics

4. **Google Drive Sync**
   - Authenticate
   - Create/update folder structure
   - Upload processed files

## ⚡️ Performance

- Asynchronous processing for parallel data extraction
- Smart batching for large datasets
- Automatic retry mechanism for resilience
- Efficient memory management for large files 