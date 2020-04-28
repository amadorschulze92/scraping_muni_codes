import pandas as pd
import sys
import numpy as np
from time import sleep
import time
import os
import glob

from scraper_tools import *
import codepub_scraper
import qcode_scraper
import muni_code_scraper


def rerun(my_funct, s3_bucket, s3_path, s3_table, base_loc, muni_tuple):
    """runs a scraper (ie my_funct) for a given muni_tuple which contains
    (city_name, link_to_munipal_code). If that scraper fails rerun will try
    to run the scraper again."""
    start = time.time()
    miss, keys_written = my_funct(s3_bucket, s3_path, s3_table, base_loc, muni_tuple)
    sleep(2)

    if miss:
        print(f'{muni_tuple[0]} has failed, rerunning')
        final, keys_written = my_funct(s3_bucket, s3_path, s3_table, base_loc, muni_tuple)
        if final:
            print(f'{muni_tuple[0]} has failed again')
            return f'{muni_tuple[0]}: {muni_tuple[1]}', []
        else:
            print('written successfully after second run')
    else:

        print(f"{muni_tuple[0]} completed in {time.time() - start} seconds")
        return '', keys_written


def main():
    cwd = os.getcwd()
    sys.path.insert(0, cwd + "/" + "chromedriver")

    og_df = pd.read_csv("my_links.csv", converters={'links': eval})
    og_df = og_df.drop("Unnamed: 0", axis=1)

    print("generating links")
    tuples_muni = muni_code_scraper.generate_municode_links()
    df_codepub = og_df.loc[og_df["link_type"] == "codepub"]
    df_qcode = og_df.loc[og_df["link_type"] == "qcode"]
    df_amlegal = og_df.loc[og_df["link_type"] == "amlegal"]
    df_other = og_df.loc[og_df["link_type"] == "other"]

    base_loc = '/Users/kjafshar/dev/test_folder/'
    s3_bucket = 'mtc-redshift-upload'
    s3_path = "test_kjafshar/"

    red_sch = "test_kjafshar"
    tbl = "cache_muni_scraping"
    red_table = red_sch + "." + tbl
    red_db = "staging"

    if check_if_table_exists_on_redshift(red_table, dbname='staging', geoserver=False):
        rs_table = redshift_status_check(red_table,red_db)
    else:
        setup_initial_table(s3_bucket,s3_path, red_table, red_db)
        rs_table = redshift_status_check(red_table, red_db)

    missed_municipal = []
    sleep(2)
    keys_written_municode = []
    for m in tuples_muni:
        print("-"*5)
        missed_municode, keys_written = rerun(muni_code_scraper.municode_scraper, s3_bucket, s3_path, rs_table, base_loc, m)
        if missed_municode:
            missed_municipal.append(missed_municode)
        else:
            keys_written_municode += keys_written

    if not missed_municipal:
        print("municode links successfully crawled")

    # get data from codepub
    missed_len = len(missed_municipal)
    keys_written_codepub = []
    for city, link in zip(df_codepub["city"], df_codepub["links"]):
        print("-"*5)
        missed_codepub, keys_written = rerun(codepub_scraper.code_pub_main, s3_bucket, s3_path, rs_table, base_loc, [city, link])
        if missed_codepub:
            missed_municipal.append(missed_codepub)
        else:
            keys_written_codepub += keys_written
    if missed_len == len(missed_municipal):
        print("code publishing links successfully crawled")

    # get data from qcode
    missed_len = len(missed_municipal)
    keys_written_qcode = []
    for city, link in zip(df_qcode["city"], df_qcode["links"]):
        print("-"*5)
        missed_qcode, keys_written = rerun(qcode_scraper.q_code_main, s3_bucket, s3_path, rs_table, base_loc, [city, link])
        if missed_qcode:
            missed_municipal.append(missed_qcode)
        else:
            keys_written_qcode += keys_written
    if missed_len == len(missed_municipal):
        print("q code links successfully crawled")

    if len(missed_municipal) > 0:
        for item in missed_municipal:
            print(item)

    for keys in [keys_written_municode, keys_written_codepub, keys_written_qcode]:

        if len(keys) > 0:
            new_table_rows = table_builder(s3_bucket, keys, rs_table)
            # append new_table_rows


if __name__ == '__main__':
    main()
