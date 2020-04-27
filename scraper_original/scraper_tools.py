import re
from datetime import datetime
import os
import sys
from selenium.webdriver.support.ui import WebDriverWait
import time
import getpass

user = getpass.getuser()
sys.dont_write_bytecode = True

sys.path.insert(0, '/Users/{}/Box/Utility Code'.format(user))

from utils_io import *


def extract_date(messy_text):
    messy_text = "\n".join(messy_text)
    if re.search('passed\s.*([A-Z].+?\d+)\.', messy_text):
        match = re.search(r'passed\s.*([A-Z].+?\d+)\.', messy_text)
        match_date = datetime.strptime(match.group(1), '%B %d, %Y').date()
    elif re.search(r'the\s(.+?)\scode\ssupplement\.', messy_text):
        match = re.search(r'the\s(.+?)\scode\ssupplement\.', messy_text)
        try:
            match_date = datetime.strptime(match.group(1), '%Y-%m').date()
        except:
            match_date = datetime.strptime(match.group(1), '%B %Y').date()
    else:
        print("could not match date")
        print(messy_text)
    return match_date.strftime('%m-%d-%y')


def make_path(base_loc, city, num_date):
    path = f"{base_loc}{city}/{num_date}/"
    try:
        print(path)
        os.makedirs(path, exist_ok=True)
    except OSError:
        print("path problems")
        if not os.path.isdir(path):
            raise
    return path


def redshift_status_check(red_tbl,red_db):

    # this function creates a pd df from the current redshift table of muni docs
    # this df is used to check the status decide how to treat crawled docs

    sql_statement = f'SELECT * FROM {red_tbl}'
    df = pull_large_df_from_redshift_sql(sql_statement, dbname=red_db)
    df.drop(columns="row_number",inplace=True)
    return df


def check_for_update(date, muni, rs_table):

    # this function will check the status df to see if the given data is more recent than the
    # most recent date in the table

    muni_dates = rs_table.loc[rs_table.muni == muni].date.sort_values(ascending=False)

    if len(muni_dates) > 0:

        most_recent = muni_dates[0]

        if date > most_recent:

            return True

        else:

            return False

    else:
        return True


def diff_score(key, table):

    # extract
    # compute diff and store as delta
    delta = None
    new_text = None
    return delta


def s3_file_writer(s3_bucket, s3_path, base_loc, muni, update_date, title, text):
    """
    This function will combine downloaded docs into a single txt

    :param base_loc: path to download folder
    :param muni: municipality name
    :param update_date: data municode updated
    :return: nothing
    """

    title = title.replace("/", '_')

    s3_key = (s3_path +
              muni + "/" +
              update_date + '/' +
              title + ".txt")

    filename = base_loc + title + '.txt'

    with open(filename, 'w') as f:
        f.write(text)

    try:
        copy_file_to_s3(filename, s3_bucket, s3_key)
        os.remove(filename)

        print('file write complete')
        print('')
        return s3_key
    # write to s3
    except:
        print(f'file issue for {filename}')
        print('')
        os.remove(filename)

    return s3_key

    # remove any docs left in download folder


def find_click_n_wait(driver, current_xpath, next_xpath, section_num, wait_time, extra_time):
    """find element click on it and wait till next xpath is present"""
    my_section = driver.find_elements_by_xpath(current_xpath)
    click_n_wait(driver, next_xpath, my_section, section_num, wait_time, extra_time)


def click_n_wait(driver, next_xpath, my_section, section_num, wait_time, extra_time):
    """click on current section and wait for next xpath to be present"""
    my_section[section_num].click()
    waiting_for_presence_of(driver, next_xpath, wait_time, extra_time)


def waiting_for_presence_of(driver, next_xpath, wait_time, extra_time):
    """wait till xpath is present, but usually needs a little extra time to load"""
    waiting = WebDriverWait(driver, wait_time).until(EC.presence_of_element_located((By.XPATH, next_xpath)))
    time.sleep(extra_time)
