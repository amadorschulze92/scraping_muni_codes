import re
import pandas as pd
import numpy as np


def make_path(base_loc, city, messy_text):
    if re.search(r'passed\s(.+?)\.', messy_text):
        match = re.search(r'passed\s(.+?)\.', messy_text)
        match_date = datetime.strptime(match.group(1), '%B %d, %Y').date()
    elif re.search(r'the\s(.+?)\scode\ssupplement\.', messy_text):
        match = re.search(r'the\s(.+?)\scode\ssupplement\.', messy_text)
        try:
            match_date = datetime.strptime(match.group(1), '%Y-%m').date()
        except:
            match_date = datetime.strptime(match.group(1), '%B %Y').date()
    num_date = match_date.strftime('%m-%d-%y')
    path = f"{base_loc}/{city}/{num_date}"
    try:
        os.makedirs(path, exist_ok=True)
    except OSError:
        if not os.path.isdir(path):
            raise
    return path
