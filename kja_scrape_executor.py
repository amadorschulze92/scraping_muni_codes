import pandas as pd
import numpy as np
import scrape_codepub
import scrape_qcode
import muni_code_scraper
from time import sleep
from time import time
import os
import glob


def rerun(my_funct, s3_bucket, s3_path, s3_table, base_loc, muni_tuple):

    start = time()
    miss = my_funct(s3_bucket, s3_path, s3_table, base_loc, muni_tuple[1])
    sleep(2)

    if miss:
        print(f'{muni_tuple[0]} has failed, rerunning')
        final = my_funct(s3_bucket, s3_path, s3_table, base_loc, muni_tuple[1])
        if len(final) > 0:
            print(f'{muni_tuple[0]} has failed again')
            return f'{muni_tuple[0]}: {muni_tuple[1]}'
        else:
            print('written successfully after second run')
    else:

        print(f"{muni_tuple[0]} completed in {time() - start} seconds")


def s3_status_check(S3_bucket, S3_path):
    return True


def main():
    og_df = pd.read_csv("my_links.csv", converters={'links': eval})
    og_df = og_df.drop("Unnamed: 0", axis=1)

    tuples_muni = muni_code_scraper.generate_municode_links()
    df_codepub = og_df.loc[og_df["link_type"] == "codepub"]
    df_qcode = og_df.loc[og_df["link_type"] == "qcode"]
    df_amlegal = og_df.loc[og_df["link_type"] == "amlegal"]
    df_other = og_df.loc[og_df["link_type"] == "other"]

    codepub = zip(df_codepub["city"], df_codepub["links"])
    qcode = zip(df_qcode["city"], df_qcode["links"])

    base_loc = '/Users/kjafshar/Documents/test_folder/'

    s3_bucket = 'mtc-redshift-upload'

    s3_path = "test_kjafshar/"

    s3_table = s3_status_check(s3_bucket, s3_path)

    missed_muni = []

    sleep(2)

    for m in tuples_muni[:1]:
        missed = rerun(muni_code_scraper.municode_scraper, s3_bucket, s3_path, s3_table, base_loc, m)
        if missed:
            missed_muni.append(missed)
        else:
            print("municode links successfully crawled")

    # missed_code_p = rerun(scrape_codepub.code_pub_main, codepub, base_loc)

    # missed_q_code = rerun(scrape_qcode.q_code_main, qcode, base_loc)

    if len(missed_muni) > 0:
        for item in missed_muni:
            print(item)


if __name__ == '__main__':
    main()
