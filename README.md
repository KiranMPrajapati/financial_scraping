# SEC Data Scraping and Cleaning Pipeline

This Python script provides an automated pipeline for scraping data from SEC websites, dividing scraped pages based on page numbers, and cleaning the extracted tables.

**Features:**

* Scrapes data from SEC websites 10Q documents.
* Divides scraped pages into individual pages for further processing.
* Cleans extracted tables and prepares them for analysis.

**Installation (if applicable):**

1. Clone this repository: `git clone https://github.com/Nishanbuyofm/financial_scraping.git`
2. Install required dependencies (`pip install -r requirements.txt`

**Usage:**

1. **(Optional) Configure input and output directories:**
   - Modify the script (`pipeline.py`) to adjust the paths for input and output data as needed.
2. Run the script: `python pipeline.py`

**Output:**

* The script generates cleaned tables from the scraped SEC data in the specified output directory (`output/table_cleaned_data/<year>`).

**Dependencies:**
* `config.py`: contain api of scrapingBee
* `scrape_page.sec_scrape`: Module containing the `scrape` function. ScrapingBee API is used and api credential need to be in config.py file
* `divide_page`: Module containing the `divide_page` function that divides html containing multiple pages into individual pages.
* `clean_table`: Module containing the `clean_table` function that cleans data like identify header, bold data, mergeing header, adding csv with metadata.

