# Penn Alumni Directory Scraper

A Python-based web scraper that extracts alumni information from the Penn Alumni Directory, specifically targeting alumni in Management Consulting.

## Features

- Automated login to MyPenn portal with DuoMobile authentication support
- Scrapes alumni profiles in batches of 100
- Extracts names and email addresses
- Saves data to CSV files
- Includes error handling and logging
- Supports pagination through offset parameter

## Prerequisites

- Python 3.x
- Chrome browser installed
- Required Python packages:
  - selenium
  - beautifulsoup4

## Installation

1. Install required packages:
```bash
uv add selenium beautifulsoup4 webdriver_manager
```

## Configuration

Edit `penn_alum_scraper.py` and set your credentials:

```python
username = "your_pennkey"
password = "your_password"
offset = 0  # Change this to start from a different page, keep it in 100s.
```

## Usage

1. Run the scraper:
```bash
uv run penn_alum_scraper.py
```

2. When prompted, approve the login request on your DuoMobile app.

3. The scraper will:
   - Log into MyPenn
   - Navigate to the directory
   - Scrape profiles in the Management Consulting industry
   - Save results to CSV files in the `output` directory

## Output

- CSV files are saved in the `output` directory
- File naming format: `penn_alumni_[start]-[end].csv`
- Each file contains:
  - Name
  - Email address

## Notes

- The scraper includes a 15-second wait for DuoMobile authentication
- Each batch processes up to 100 profiles
- The scraper includes warm-up navigation to ensure proper loading
- Error handling is implemented for various scenarios

## Limitations

- Only scrapes Management Consulting industry profiles
- Requires manual DuoMobile authentication
- Limited to 100 profiles per run
- May need adjustments if the MyPenn interface changes
