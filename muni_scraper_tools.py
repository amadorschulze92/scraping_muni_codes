import re
from datetime import datetime
import os
import sys

sys.path.insert(0, "../Utility Code/")
from utils_io import *


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


def s3_status_check(S3_bucket, S3_path):
    return True


def check_for_s3_delta(muni, title, text, s3_table):
    return True


def s3_file_writer(s3_bucket, s3_path, s3_table, base_loc, muni, update_date, title, text):
    """
    This function will combine downloaded docs into a single txt

    :param base_loc: path to download folder
    :param output_dir: path to output directory
    :param i: given index of doc
    :param muni: municipality name
    :param update_date: data municode updated
    :param names: list of article names for given muni
    :return: nothing
    """

    s3_key = (s3_path +
              muni + "/" +
              update_date + '/' +
              title + ".txt")

    filename = base_loc + title + '.txt'

    if check_for_s3_delta(muni, title, text, s3_table):
        with open(filename, 'w') as f:
            f.write(text)

        try:
            copy_file_to_s3(filename, s3_bucket, s3_key)
            os.remove(filename)
            print('file write complete')
            print('')
        # write to s3
        except:
            print(f'file issue for {filename}')
            print('')
            os.remove(filename)

    else:
        print("doc hasn't changed")
        print('')

    # remove any docs left in download folder

