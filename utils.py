import re
import pandas as pd

def split_with_regex(text):
  """Splits a string based on "})" but includes "})" in the substrings using regex.
  Args:
      text: The string to split.
  Returns:
      A list of substrings.
  """
  pattern = r"(.*?}\)),?"  # Capture everything followed by "})"
  return re.findall(pattern, text)

def csv_string_to_df(csv_data):
    output = []
    lines = csv_data.strip().split('\n')
    for line in lines:
        split_text = split_with_regex(line)
        output.append(split_text)
    df = pd.DataFrame(output)
    return df

