import os
from divide_page.scraping_logic import divide_page
from clean_table.clean_table import clean_table
from scrape_page.sec_scrape import scrape

year = '2021'

# For Scrapping
# input_dir = f'{os.getcwd()}/output/companies_details/companies_details.parquet'
# output_dir = f'{os.getcwd()}/output/scraped_data/{year}'
# scrape(input_dir, output_dir)

# For Dividing page
# input_dir = f'{os.getcwd()}/output/scrapped_data/{year}'
# output_dir = f'{os.getcwd()}/output/page_divided_data/{year}_pages'
# divide_page(input_dir, output_dir)


# For Cleaning table
input_dir = f'{os.getcwd()}/output/page_divided_data/{year}_pages'
output_dir = f'{os.getcwd()}/output/table_cleaned_data/{year}'
clean_table(input_dir, output_dir)