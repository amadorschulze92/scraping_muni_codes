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
            return f'{muni_tuple[0]}: {muni_tuple[1]}', keys_written
        else:
            print('written successfully after second run')
            return '', keys_written
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

    base_loc = '/Users/kjafshar/dev/MTC-Work/temp_folder/'
    s3_bucket = 'mtc-redshift-upload'
    s3_path = "test_kjafshar/"

    red_sch = "test_kjafshar"
    tbl = "muni_scraping"
    red_table = red_sch + "." + tbl
    cache_table = ".cache_".join(red_table.split("."))
    red_db = "staging"

    if check_if_table_exists_on_redshift(red_table, dbname='staging', geoserver=False):
        rs_table = redshift_status_check(red_table,red_db)
    else:
        setup_initial_table(s3_bucket,s3_path, red_table, red_db)
        rs_table = redshift_status_check(red_table, red_db)

    # get data from municode
    missed_municipal = []
    muni_missed_municipal = []
    sleep(2)
    keys_written_municode = []
    for m in tuples_muni:
        print("-"*5)
        missed_municode, keys_written = rerun(muni_code_scraper.municode_scraper, s3_bucket, s3_path, rs_table, base_loc, m)
        if missed_municode:
            muni_missed_municipal.append(missed_municode)
            keys_written_municode += keys_written
        else:
            keys_written_municode += keys_written

    if not muni_missed_municipal:
        print("municode links successfully crawled")

    else:
        rerun_muni_tuples = [i.split(": ") for i in muni_missed_municipal]
        for m in rerun_muni_tuples:
            print("-" * 5)
            missed_municode, keys_written = rerun(muni_code_scraper.municode_scraper, s3_bucket, s3_path, rs_table, base_loc, m)
            if missed_municode:
                missed_municipal.append(missed_municode)
                for key in keys_written:
                    if key not in keys_written_municode:
                        keys_written_municode += keys_written
            else:
                for key in keys_written:
                    if key not in keys_written_municode:
                        keys_written_municode += keys_written

    if len(keys_written_municode) > 0:
        new_table_rows = table_builder(s3_bucket, keys_written_municode, rs_table)
        create_doc_table(new_table_rows, s3_bucket, cache_table, red_db)
        append_new_rows(cache_table, red_table, red_db)


    # get data from codepub
    missed_len = len(missed_municipal)
    codepub_missed_municipal = []
    keys_written_codepub = []
    for city, link in list(zip(df_codepub["city"], df_codepub["links"])):
        print("-"*5)
        missed_codepub, keys_written = rerun(codepub_scraper.code_pub_main, s3_bucket, s3_path, rs_table, base_loc, [city, link])
        if missed_codepub:
            codepub_missed_municipal.append(missed_codepub)
        else:
            keys_written_codepub += keys_written
    if not codepub_missed_municipal:
        print("code publishing links successfully crawled")
    else:
        rerun_codepub_tuples = [i.split(": ") for i in codepub_missed_municipal]
        for city, link in rerun_codepub_tuples:
            print("-" * 5)
            link = [link.replace("[\'","").replace("\']","")]
            missed_codepub, keys_written = rerun(codepub_scraper.code_pub_main, s3_bucket, s3_path, rs_table, base_loc, [city, link])
            if missed_codepub:
                missed_municipal.append(missed_codepub)
                for key in keys_written:
                    if key not in keys_written_codepub:
                        keys_written_codepub += keys_written
            else:
                for key in keys_written:
                    if key not in keys_written_codepub:
                        keys_written_codepub += keys_written

    keys_written_codepub = [key for key in keys_written_codepub if key not in rs_table.s3_key.to_list()]
    if len(keys_written_codepub) > 0:
        new_table_rows = table_builder(s3_bucket, keys_written_codepub, rs_table)
        create_doc_table(new_table_rows, s3_bucket, cache_table, red_db)
        append_new_rows(cache_table, red_table, red_db)


    # get data from qcode
    missed_len = len(missed_municipal)
    keys_written_qcode = []
    for city, link in list(zip(df_qcode["city"], df_qcode["links"])):
        print("-"*5)
        missed_qcode, keys_written = rerun(qcode_scraper.q_code_main, s3_bucket, s3_path, rs_table, base_loc, [city, link])
        if missed_qcode:
            missed_municipal.append(missed_qcode)
        else:
            keys_written_qcode += keys_written
    if missed_len == len(missed_municipal):
        print("q code links successfully crawled")
    keys_written_qcode = [key for key in keys_written_qcode if key not in rs_table.s3_key.to_list()]
    if len(keys_written_qcode) > 0:
        new_table_rows = table_builder(s3_bucket, keys_written_qcode, rs_table)
        create_doc_table(new_table_rows, s3_bucket, cache_table, red_db)
        append_new_rows(cache_table, red_table, red_db)

    # get data from amlegal (aka SF)
    missed_len = len(missed_municipal)
    keys_written_amlegal = []
    city = 'san francisco'
    link = 'https://codelibrary.amlegal.com/codes/san_francisco/latest/overview'
    print("-"*5)
    missed_amlegal, keys_written = rerun(qcode_scraper.q_code_main, s3_bucket, s3_path, rs_table, base_loc, [city, link])
    if missed_amlegal:
        missed_municipal.append(missed_amlegal)
    else:
        keys_written_amlegal += keys_written
    if missed_len == len(missed_municipal):
        print("amlegal link successfully crawled")

    keys_written_amlegal = [key for key in keys_written_amlegal if key not in rs_table.s3_key.to_list()]
    if len(keys_written_amlegal) > 0:
        new_table_rows = table_builder(s3_bucket, keys_written_amlegal, rs_table)
        create_doc_table(new_table_rows, s3_bucket, cache_table, red_db)
        append_new_rows(cache_table, red_table, red_db)




    # display which municipals failed
    if len(missed_municipal) > 0:
        for item in missed_municipal:
            print(item)


if __name__ == '__main__':
    main()
