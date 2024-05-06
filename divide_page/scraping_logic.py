import os
import re
from datetime import datetime
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor
import pandas as pd
import pyarrow
from pandas import DataFrame
from logger_file import logger

def save_dataframepqt_pd(df: DataFrame, path: str):
    df.to_parquet(f"{path}.parquet", index=False)

def modified_split(cik_name: str, date: str, url, contents):
    page_splitted = []
    pages_with_tables = []
    page_number = 0
    matching_elements = []
    try:
        soup = BeautifulSoup(contents, 'html.parser')
        soupbody = soup.body
        try:
            headers = soupbody.find_all('ix:header')
            for header in headers:
                header.extract()
        except Exception as e:
            print(e)
        pattern = re.compile(r"(?:page-break-after:\s*always|page-break-before:\s*always|break-before:\s*page)", re.IGNORECASE)
        for tag in soupbody.find_all(True, recursive=True): 
            if 'style' in tag.attrs and pattern.search(tag['style']):
                matching_elements.append(tag)

        if not matching_elements:
            pages_with_tables.append({
                "cik_name": cik_name,
                "reporting_date": date,
                "url": url,
                "page_number": page_number,
                "page_content": "empty soup"
            })
            return pages_with_tables
        
        elif matching_elements:
            current_position = 0
            soup_contents = str(soupbody)
            matching_str = [str(element) for element in matching_elements]

            for match in matching_str:
                while match in soup_contents[current_position:]:
                    next_occurrence = soup_contents[current_position:].find(match)
                    page_splitted.append(soup_contents[current_position:current_position + next_occurrence])
                    current_position += next_occurrence + len(match)

            if current_position < len(soup_contents):
                page_splitted.append(soup_contents[current_position:])

        if len(page_splitted) != len(matching_str)+1:
            pages_with_tables.append({
                "cik_name": cik_name,
                "reporting_date": date,
                "url": url,
                "page_number": page_number,
                "page_content": 'empty soup'
            })
            return pages_with_tables
        for page_content in page_splitted:
            page_number += 1
            soup = BeautifulSoup(page_content, "html.parser")
            table_tags = soup.find_all("table")

            if table_tags:
                table_text_lengths = [len(tag.get_text(strip=True)) for tag in table_tags]

                if any(length > 35 for length in table_text_lengths):
                    page_content = str(soup)

                pages_with_tables.append({
                    "cik_name": cik_name,
                    "reporting_date": date,
                    "url": url,
                    "page_number": page_number,
                    "page_content": page_content
                })
        return pages_with_tables
        
    except Exception as e:
        logger.info(f"An error occured:", e)
    return None

def sort_key(filename):
    return int(filename.split('_')[1].split('.')[0])

def divide_page(data_dir, output_dir):
    logger.info("Cleaning contents Started")
    batches = os.listdir(data_dir)
    file_names = sorted(batches, key=sort_key)
    for filename in file_names[:35]:
        if filename.endswith(".parquet"):
            logger.info(f"Processing file: {filename}")
            input_file_path = os.path.join(data_dir, filename)
            df = pd.read_parquet(input_file_path)
            
            all_table_df = []
            df = df[df["contents"] != "No Soup! Got Value other than 200"]
            df = df.drop_duplicates(subset=['url'])
            form_description_links = df.to_dict(orient="records")
            
            for form_description_link in form_description_links:
                cik_name = form_description_link["cik_name"]
                date = form_description_link["reporting_date"]
                url = form_description_link["url"]
                contents = form_description_link["contents"]
                
                tables = modified_split(cik_name, date, url, contents)
                logger.info(f"Cleaned the document from {url} of the CIK name {cik_name}!!")
                
                table_df = pd.DataFrame(tables)
                all_table_df.append(table_df)
                logger.info(f"appended the document to the pool!!")
            
            final_table_df = pd.concat(all_table_df, ignore_index=True)
            final_table_df = final_table_df[final_table_df["page_content"] != "empty soup"]
            
            input_file_name = os.path.splitext(os.path.basename(input_file_path))[0]
            
            output_file_path = f"{output_dir}/{input_file_name}"
            save_dataframepqt_pd(final_table_df, output_file_path)
            logger.info(f"{input_file_name} Saved to {output_file_path}!!")

if __name__ == "__main__":
    data_dir = f'{os.getcwd()}/output/scrapped_data/2021'
    output_dir = f'{os.getcwd()}/output/page_divided_data/2021_pages'
    divide_page(data_dir, output_dir)
