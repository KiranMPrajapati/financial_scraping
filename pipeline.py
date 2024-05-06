import os
from divide_page.scraping_logic import divide_page
from clean_table.clean_table import clean_table
from scrape_page.sec_scrape import scrape

year = '2018'

# For Scrapping
# input_dir = f'{os.getcwd()}/output/companies_details/companies_details.parquet'
# output_dir = f'{os.getcwd()}/output/scraped_data/{year}'
# scrape(input_dir, output_dir)

print(f"Dividing page for year {year}")

# For Dividing page
input_dir = f'{os.getcwd()}/output/scraped_data/{year}'
output_dir = f'{os.getcwd()}/output/page_divided_data/{year}_pages'
if not os.path.exists(input_dir):
    os.makedirs(input_dir)
if not os.path.exists(output_dir):
    os.makedirs(output_dir)
divide_page(input_dir, output_dir)

print("Cleaning table for year", year)

# For Cleaning table
input_dir = f'{os.getcwd()}/output/page_divided_data/{year}_pages'
output_dir = f'{os.getcwd()}/output/table_cleaned_data/{year}'
if not os.path.exists(input_dir):
    os.makedirs(input_dir)
if not os.path.exists(output_dir):
    os.makedirs(output_dir)
clean_table(input_dir, output_dir)