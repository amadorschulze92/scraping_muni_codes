from muni_code_scraper import *
# from gen_scraper import *

HOME_DIR = '/Users/kjafshar/Documents/'


def rerun(func, base_loc, links=None):

    miss = func(base_loc, links)
    if miss:
        print(f'these indices failed {miss}')
        final = func(base_loc, miss)
        if final:
            print(f'these indices failed again {final}')
        else:
            print('written successfully after second run')
    else:
        print('fully written successfully')


def main():

    rerun(municode_scraper, HOME_DIR, [0])

    # rerun(gen_scraper, HOME_DIR)


if __name__ == "__main__":
    main()