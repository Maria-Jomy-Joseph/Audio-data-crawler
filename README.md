# Audio-data-crawler
This Python script automates the download of audiobook MP3 files from the website "albalearning.com/audiolibros". It retrieves the links from the root webpage, visits corresponding sites, and downloads the MP3 files.

# Requirements

- Python 3.x
- BeautifulSoup (pip install beautifulsoup4)
- tqdm (pip install tqdm)
- pydub (pip install pydub)
- psycopg2 (pip install psycopg2-binary)

# Usage

- Ensure you have the required libraries installed.
- Modify the script variables as needed:
- web_root: Root URL of the audiobooks website.
- author_keywords: List of keywords representing authors on the website.
- Run the script (python script_name.py).

# Functionality

calculate_quality: Uses the Signal-to-Noise Ratio (SNR) to estimate audio quality. Adjustments may be needed for a more sophisticated quality assessment.

download_mp3_files: Downloads MP3 files from provided links, organizes them into folders, calculates audio quality, and inserts records into a PostgreSQL database.

insert_into_database: Inserts audio file information into a PostgreSQL database. Modify the connection details and SQL query as needed.

Other functions: Various utility functions for link extraction, filtering, and setting variables.

# Database Connection

Modify the PostgreSQL connection details in the insert_into_database function.
