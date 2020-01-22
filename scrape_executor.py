import pandas as pd
import numpy as np
import scrape_codepub
import scrape_qcode


def rerun(my_funct, links, base_loc):
    missed = my_funct(links, base_loc)
    if len(missed) == 0:
        return "All cities completed"
    print("\nRe-run missing cities\n")
    missed_again = my_funct(missed, base_loc)
    return missed_again


def main():
    og_df = pd.read_csv("my_links.csv", converters={'links': eval})
    og_df = og_df.drop("Unnamed: 0", axis=1)

    df_muni = og_df.loc[og_df["link_type"] == "municode"]
    df_codepub = og_df.loc[og_df["link_type"] == "codepub"]
    df_qcode = og_df.loc[og_df["link_type"] == "qcode"]
    df_amlegal = og_df.loc[og_df["link_type"] == "amlegal"]
    df_other = og_df.loc[og_df["link_type"] == "other"]

    codepub = zip(df_codepub["city"], df_codepub["links"])
    qcode = zip(df_qcode["city"], df_qcode["links"])

    base_loc = '/Users/mschulze/Documents/test_selenium'

    missed_cp = rerun(scrape_codepub.code_pub_main, codepub, base_loc)
    print(missed_cp)

    missed_qc = rerun(scrape_qcode.q_code_main, qcode, base_loc)
    print(missed_qc)


if __name__ == '__main__':
  main()
