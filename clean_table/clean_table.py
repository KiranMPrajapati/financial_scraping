import pandas as pd
from bs4 import BeautifulSoup
import csv, os
import re
import numpy as np
from IPython.display import display

def remove_duplicate_columns(df, preserve_last_n=4):
    if df.shape[0]<3:
        return pd.DataFrame()
    
    df_transposed = df.T
    preserve_columns = df_transposed.index[-preserve_last_n:]
    duplicated = df_transposed[df_transposed.index.isin(preserve_columns) == False].duplicated()
    columns_to_drop = duplicated[duplicated].index.tolist()
    df = df.drop(columns=columns_to_drop)
    return df

def sort_key(filename):
    return int(filename.split('_')[1].split('.')[0])

def convert_to_pt(value):
    try:
        unit = value[-2:]
        val = float(value[:-2])
        if unit == 'pt':
            val= val
        elif unit == 'px':
            val = val * 0.75  # 1 pixel is approximately 0.75 points
        elif unit == 'em':
            val = val * 12  # 1 em is equivalent to 12 points by default
        elif unit == 'in':
            val = val * 72  # 1 inch is equal to 72 points
        return round(val)
    except:
        return int(value)
    
    
def assign_tab_labels(df, label_prefix='t'):
    header_col = df.columns[-1]
    tab_col = df.columns[-2]
    df['tab_labels'] = np.where(
        df[header_col] == 0,
        pd.Series(df[tab_col]).rank(method='dense').astype(int).apply(lambda x: f"{label_prefix}{x}"),
        np.nan
    )
    return df

def clean_table_element(table_element): 
    df = pd.DataFrame()
    tab_pattern = r"""
        (?:margin-left|padding-left|text-indent)\s*:\s*(\-?\d+(?:\.\d+)?(?:pt|px|em|in)?)  # Match margin-left, padding-left, text-indent
        |
        (?:padding|margin)\s*:\s*(?:\-?\d+(?:\.\d+)?(?:pt|px|em|in)?\s+){3}(\d+(?:\-?\.\d+)?(?:pt|px|em|in)?)  # Match padding or margin (last value)
    """

    bold_pattern = r"font-weight:bold|color:\#000000"
    
    if table_element:
        table_data = []
        previous_value = ''
        for row in table_element.find_all('tr'):
            if row.find_all(['td', 'th']):
                row_data = []
                is_colspan = 0
                tab_value = 0
                bold = 0
                for cell_idx, cell in enumerate(row.find_all(['td', 'th'])):
                    cell_value = cell.get_text(strip=True)
                    # Handle special cases
                    if previous_value in ["$", "€", "E"]:
                        cell_value = previous_value + cell_value
                    elif previous_value == '(':
                        cell_value = f'({cell_value})'

                    if cell_value in ["$", "€", "E"]:
                        previous_value = cell_value
                        cell_value = ''
                    elif cell_value == '%' and cell_idx == 0:
                        previous_value = cell_value
                    elif cell_value in ["%", ")%"]:
                        row_data[-1] = previous_value + "%"
                        cell_value = ''
                        previous_value = '%'
                    elif cell_value == '(':
                        cell_value = ''
                        previous_value = '('
                    elif cell_value == ')':
                        cell_value = ''
                        previous_value = ')'
                    elif re.search(r'\(\d+\b', cell_value) and not cell_value.endswith(')'):
                        cell_value = cell_value + ')'
                        previous_value = cell_value
                    else:
                        previous_value = cell_value

                    if cell_idx == 0 and re.findall(tab_pattern, str(cell), re.VERBOSE):
                        matches = re.findall(tab_pattern, str(cell), re.VERBOSE)
                        values = [convert_to_pt(match) for match in matches for match in match if match]
                        tab_value = int(sum(values))

                    if cell_idx == 0 and re.findall(bold_pattern, str(cell), re.VERBOSE):
                        # print(cell_value, "bold")
                        # print(re.findall(bold_pattern, str(cell), re.VERBOSE))
                        bold = 1

                    if "colspan" in str(cell):
                        try:
                            is_colspan = 1
                            col = re.findall(r'colspan="(\d+)"', str(cell))[0]
                            row_data.extend([cell_value]*(int(col) - 1))
                        except:
                            pass
                    row_data.append(cell_value)
                
                # Append the colspan flag to the row data
                row_data.append(bold)
                row_data.append(tab_value)
                row_data.append(is_colspan)
                table_data.append(row_data)
            
        df = pd.DataFrame(table_data).replace('', np.nan)
        df = remove_duplicate_columns(df)
    return df

def drop_null_values(df, rows_to_keep = 5):
    # Drop null rows excluding the last four columns
    df = df.dropna(axis = 0, how = 'all', subset=df.columns[:-4])
    # Get df excluding last four columns and Drop columns if the data below rows_to_keep is null
    df1 = df[df.columns[:-4]].dropna(axis=1, how='all', subset=df.index[rows_to_keep:])
    df2 = df[df.columns[-4:]]
    # Concatenate along the columns axis to ensure proper alignment
    df = pd.concat([df1, df2], axis=1, join='outer')
    return df

def write_html(html_content, file_name):
    soup = BeautifulSoup(html_content, "html.parser")
    with open(file_name, "w", encoding="utf-8") as f:
        f.write(str(soup.prettify()))

def dataframe_to_html(df):
    css_dict = df[~df['tab_labels'].isna()].drop_duplicates('tab_labels', keep='first').set_index('tab_labels')[df.columns[-3]].to_dict()
    print(css_dict)
    css_styles = ""
    for class_name, padding_left in css_dict.items():
        css_styles += f".{class_name} {{ padding-left: {padding_left}; }}\n"
    css = f"<style>\n{css_styles}</style>"

    df = df.fillna('').astype(str)
    html_table = '<table>\n'
    for idx, row in df.iterrows():
        html_table += '<tr>'
        cell_tag = 'th' if row[df.columns[-2]] == '1' else 'td'
        label = row['tab_labels']
        class_name = f' class="{label}"' if label else ''
        for i, val in enumerate(row[:-4]):
            if class_name and i == 0:
                html_table += f'<{cell_tag}{class_name}>{val}</{cell_tag}>'
            else:
                html_table += f'<{cell_tag}>{val}</{cell_tag}>'
    html_table += '</table>'
    
    return html_table, css


def get_csv_string(df):
    #drop last column
    csv_string_with_header = df.to_csv(index=False, header=False)
    if not df.empty:
        df = df.drop(df.columns[-4:], axis=1)
    csv_string = df.to_csv(index=False, header=False)
    return csv_string, csv_string_with_header  

def combine_header_rows(df, header_col):
    df = df.replace(np.nan, '').astype(str)
    df1 = df[df[header_col] == '1']
    if not df1.empty:
        df2 = df[df[header_col] == '0']
        df1 = df1.groupby(header_col).agg(' '.join).reset_index()
        df1 = df1.reindex(columns = df2.columns).replace(r'^\s*$', np.nan, regex=True)
        df1.iloc[0, -3] = 0
        df1.iloc[0, -4] = 1 if '1' in df1.iloc[0, -4] else 0
        df = pd.concat([df1, df2])
    return df       

def add_csv_metadata(csv_string_with_header):
    lines = csv_string_with_header.strip().split('\n')
    reader = csv.reader(lines)
    data = []
    for row in reader:
        data.append(row)
    resverse_data = data[::-1]
    size_of_data = len(resverse_data)
    for i, row in enumerate(resverse_data):
        indent_value = row[-3]
        tab_value = row[-1]
        bold = row[-4]
        if indent_value == '0':
            parent_cell_idx = ''
            parent_cell_value = ''
        else:
            for j, next_rows in enumerate(resverse_data[i+1:]):
                next_indent_value = next_rows[-3]
                if next_indent_value == indent_value or next_indent_value > indent_value or next_rows[0] == "":
                    continue
                else:
                    parent_cell_idx = (size_of_data- (i+1)- (j+1), 0)
                    parent_cell_value = next_rows[0]
                    break
        for idx, cell_value in enumerate(row[:-4]):
            meta_data = {
                "indent": tab_value,
                "parent_cell_value": parent_cell_value,
                "parent_cell_idx": parent_cell_idx,
                "bold": bold}
            new_cell_value = (cell_value, meta_data)
            row[idx] = new_cell_value
    csv_with_metadata, csv_with_indent_bold, csv_with_indent_parent = '', '', ''
    for row in data:
        # Create three new lists with modified metadata dictionaries
        list_with_all_metadata = [(string_value, metadata) for string_value, metadata in row[:-4]]
        # Remove the 'bold' key from the metadata dictionaries
        list_with_indent_and_parent = [(string_value, {key: value for key, value in metadata.items() if key != 'bold'}) for string_value, metadata in row[:-4]]
        # Remove the 'parent_cell_value' key from the metadata dictionaries
        list_with_indent_and_bold = [(string_value, {key: value for key, value in metadata.items() if key != 'parent_cell_value' and key != 'parent_cell_idx'}) for string_value, metadata in row[:-4]]
        csv_with_metadata+=','.join(str(item) for item in list_with_all_metadata)
        csv_with_metadata+="\n"

        csv_with_indent_bold+=','.join(str(item) for item in list_with_indent_and_bold)
        csv_with_indent_bold+="\n"

        csv_with_indent_parent+=','.join(str(item) for item in list_with_indent_and_parent)
        csv_with_indent_parent+="\n"

    return csv_with_metadata, csv_with_indent_bold, csv_with_indent_parent 

def replace_with_clean_table(row):
    html_content = row['page_content']
    url = row['url']
    soup = BeautifulSoup(html_content, "html.parser")
    tables = soup.find_all('table')
    print(len(tables))
    multiple_tables = 1 if len(tables) > 1 else 0
    csv_string, csv_string_with_header = '', ''
    csv_with_metadata, csv_with_indent_bold, csv_with_indent_parent = '', '', ''
    empty = 0
    for table_element in tables:
        print(url, row['page_number'])
        df = clean_table_element(table_element)
        
        print("**************************************************")
        try:
            if not df.empty:
                df = assign_tab_labels(df, label_prefix='t')
                rows_to_keep = df[df[df.columns[-2]] == 1].shape[0]+1
                header_per = rows_to_keep/df.shape[0]*100
                if rows_to_keep > 6 or header_per > 70:
                    return pd.Series(['', '', '', '', '', '', multiple_tables])
                rows_to_keep = min(5, rows_to_keep)
                df_without_null = drop_null_values(df, rows_to_keep)
                if df_without_null.empty:
                    empty+=1
                    html_content = html_content.replace(str(table_element), '')
                else:
                    df_without_null = combine_header_rows(df_without_null, df_without_null.columns[-2])
                    csv_string1, csv_string_with_header1 = get_csv_string(df_without_null)
                    csv_string+=csv_string1
                    csv_string_with_header+=csv_string_with_header1

                    csv_with_metadata1, csv_with_indent_bold1, csv_with_indent_parent1 = add_csv_metadata(csv_string_with_header1)
                    csv_with_metadata+=csv_with_metadata1
                    csv_with_indent_bold+=csv_with_indent_bold1
                    csv_with_indent_parent+=csv_with_indent_parent1
                    
                    html, css = dataframe_to_html(df_without_null)
                    # print(html)
                    #replace table in html_content with new html
                    html_content = f"<head>\n{css}\n</head>\n{html_content}"
                    html_content = html_content.replace(str(table_element), html) if html else ''
            else:
                empty+=1
                html_content = html_content.replace(str(table_element), '')
        except:
            return pd.Series(['', '', '', '', '', '', multiple_tables])
    if len(tables) == empty:
        return pd.Series(['', '', '', '', '', '', multiple_tables])
    return pd.Series([html_content, csv_string, csv_string_with_header, csv_with_metadata, csv_with_indent_bold, csv_with_indent_parent, multiple_tables])

def clean_table(data_dir, output_dir):
    batches = os.listdir(data_dir)
    batches = sorted(batches, key=sort_key)
    # batches = ["Batch_0.parquet"]
    for batch in batches[74:]:
        df = pd.read_parquet(f'{data_dir}/{batch}')
        df = df[df['page_number']>2]
        # df[['clean_content', 'csv_string', 'csv_string_with_header', 'multiple_tables']] = df['page_content'].apply(replace_with_clean_table)
        df[['clean_content', 'csv_string', 'csv_string_with_header','csv_with_metadata', 'csv_with_indent_bold', 'csv_with_indent_parent', 'multiple_tables']] = df.apply(replace_with_clean_table, axis =1)
        df = df[df['clean_content'] != '']
        df = df.reset_index()
        df.to_parquet(f'{output_dir}/{batch}', index=False)

if __name__ == "__main__":
    input_dir = f'{os.getcwd()}/output/page_divided_data/2021_pages'
    output_dir = f'{os.getcwd()}/output/table_cleaned_data/2021'
    clean_table(input_dir, output_dir)