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
    miss = my_funct(s3_bucket, s3_path, s3_table, base_loc, muni_tuple)
    sleep(2)

    if miss:
        print(f'{muni_tuple[0]} has failed, rerunning')
        final = my_funct(s3_bucket, s3_path, s3_table, base_loc, muni_tuple)
        if final:
            print(f'{muni_tuple[0]} has failed again')
            return f'{muni_tuple[0]}: {muni_tuple[1]}'
        else:
            print('written successfully after second run')
    else:

        print(f"{muni_tuple[0]} completed in {time.time() - start} seconds")


def main():
    cwd = os.getcwd()
    sys.path.insert(0,cwd + "/" + "chromedriver")

    og_df = pd.read_csv("my_links.csv", converters={'links': eval})
    og_df = og_df.drop("Unnamed: 0", axis=1)

    print("generating links")
    tuples_muni = muni_code_scraper.generate_municode_links()
    df_codepub = og_df.loc[og_df["link_type"] == "codepub"]
    df_qcode = og_df.loc[og_df["link_type"] == "qcode"]
    df_amlegal = og_df.loc[og_df["link_type"] == "amlegal"]
    df_other = og_df.loc[og_df["link_type"] == "other"]

    base_loc = '/Users/kjafshar/Documents/test_folder/'
    s3_bucket = 'mtc-redshift-upload'
    s3_path = "test_kjafshar/"
    s3_table = s3_status_check(s3_bucket, s3_path)

    missed_municipal = []
    sleep(2)
    for m in tuples_muni:
        print("-"*5)
        missed_municode = rerun(muni_code_scraper.municode_scraper, s3_bucket, s3_path, s3_table, base_loc, m)
        if missed_municode:
            missed_municipal.append(missed_municode)
    if not missed_municipal:
        print("municode links successfully crawled")

    for city, link in zip(df_codepub["city"], df_codepub["links"]):
        print("-"*5)
        missed_codepub = rerun(codepub_scraper.code_pub_main, s3_bucket, s3_path, s3_table, base_loc, [city, link])
        if missed_codepub:
            missed_municipal.append(missed_codepub)
        else:
            print("code publishing links successfully crawled")

    for city, link in zip(df_qcode["city"], df_qcode["links"]):
        print("-"*5)
        missed_qcode = rerun(qcode_scraper.q_code_main, s3_bucket, s3_path, s3_table, base_loc, [city, link])
        if missed_qcode:
            missed_municipal.append(missed_qcode)
        else:
            print("q code links successfully crawled")

    if len(missed_municipal) > 0:
        for item in missed_municipal:
            print(item)


if __name__ == '__main__':
    main()
