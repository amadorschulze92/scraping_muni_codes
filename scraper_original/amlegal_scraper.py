import pandas as pd
import numpy as np
import re
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import time
import random
from bs4 import BeautifulSoup
import requests
import sys
import os
import scraper_tools
import glob
from time import sleep


def amlegal_main(s3_bucket, s3_path, rs_table, base_loc, start_link):
    cwd = os.getcwd()
    chrome_options = webdriver.ChromeOptions()
    # set download folder
    # configure multiple file download and turn off prompt
    prefs = {'download.default_directory': base_loc,
             'profile.default_content_setting_values.automatic_downloads': 1,
             'download.prompt_for_download': 'false',
             'default_content_settings.automatic_downloads': 1,
             'profile.content_settings.exceptions.automatic_downloads': 1}
    chrome_options.add_experimental_option('prefs', prefs)
    keys_written = []
    date_xpath = "//div[@class='currency-info']"
    lvl_1_xpath = "//div[@class='codenav__toc roboto']/div/div/a[@class='toc-link']"
    lvl_2_xpath = "//div[@class='codenav__toc roboto']/div/div/div/div/a[@class='toc-link']"
    collapse_xpath = "//div[@class='codenav__toc roboto']/div/div/button[@class='toc-caret dropdown-toggle btn-toggle']"
    download_xpath = "//button[@class='btn btn-white-circle']"
    checkedbox_xpath = "//label[@class='toc-link check--partial form-check-label']"
    checkbox_xpath = "//div[@class='toc-entry toc-entry--code']/div/div/label[@class='toc-link form-check-label']"
    pull_file_xpath = "//button[@class='btn btn-primary']"
    file_type_xpath = "//button[@class='export-button btn btn-export']"
    final_download_xpath = "//a[@class='btn btn-secondary request__open']"
    clear_downloads_xpath = "//div[@class='react-tabs__tab-panel react-tabs__tab-panel--selected']/div/div/span/button[@class='btn btn-primary']"
    city = start_link[0]
    links = start_link[1]
    print(city)
    for link in links:
        try:
            driver = webdriver.Chrome(f'{cwd}/chromedriver', options=chrome_options)
            print(link)
            driver.get(link)
            # get date
            messy_date = driver.find_elements_by_xpath(date_xpath)
            match = re.search(r'effective\s(\D+\d+,\s\d+).', messy_date[0].text)
            match_date = datetime.strptime(match.group(1), '%B %d, %Y').date()
            my_date = match_date.strftime('%m-%d-%y')
            # collect the sections
            lvl_1_section = driver.find_elements_by_xpath(lvl_1_xpath)
            collapse_buttons = driver.find_elements_by_xpath(collapse_xpath)
            download_buttons = driver.find_elements_by_xpath(download_xpath)
            for sec1_num in range(len(driver.find_elements_by_xpath(lvl_1_xpath))):
                level_1_title = lvl_1_section[sec1_num].text
                print(level_1_title)
                scraper_tools.click_n_wait(driver, lvl_1_xpath, lvl_1_section, sec1_num, 10, 4)
                scraper_tools.click_n_wait(driver, download_xpath, download_buttons, 2, 10, 2)
                # if last section go straight to downloading cuz this section is bugged
                if sec1_num < len(driver.find_elements_by_xpath(lvl_1_xpath)) - 1:
                    # click once to de-select everything...
                    scraper_tools.click_single_wait(driver, checkedbox_xpath, 2, num=0)
                    # ...and again to select everything
                    scraper_tools.click_single_wait(driver, checkbox_xpath, 2, num=sec1_num)
                else:
                    time.sleep(3)
                # click proceed button
                scraper_tools.click_single_wait(driver, pull_file_xpath, 2)
                # check if they ask to clear data we've downloaded so far
                if len(driver.find_elements_by_xpath(clear_downloads_xpath)) > 0:
                    clear_downloads = driver.find_elements_by_xpath(clear_downloads_xpath)
                    clear_downloads[0].click()
                # click type of file you want downloaded
                file_type = driver.find_elements_by_xpath(file_type_xpath)
                scraper_tools.click_n_wait(driver, final_download_xpath, file_type, 2, 300, 5)
                # click the most recent download when it is finished downloading
                for i in range(60):
                    final_download = driver.find_elements_by_xpath(final_download_xpath)
                    if len(final_download) == 2 or sec1_num == 0:
                        break
                    else:
                        time.sleep(5)
                scraper_tools.click_n_wait(driver, final_download_xpath, final_download, 0, 10, 3)
                # rename and move downloaded file
                name_sec = (sec1_num%3)+1
                old_path = base_loc+city.replace(' ', '_')+"-ca-"+str(name_sec)+".txt"
                old_path = scraper_tools.downloads_done(old_path, 36)
                path = scraper_tools.make_path(base_loc, city, my_date)
                new_path = path+city+"_"+level_1_title+".txt"
                os.rename(old_path, new_path)
                # collapse past sections of toc to reduce website slowdown
                scraper_tools.click_n_wait(driver, collapse_xpath, collapse_buttons, sec1_num, 10, 3)
                # move text to s3
                with open("new_row", 'r') as f:
                    lvl1_text = f.readlines()
                key = scraper_tools.s3_file_writer(s3_bucket, s3_path, base_loc, city, update_date, level_1_title, '\n'.join(lvl1_text))
                if key and (key not in list(rs_table.s3_key)):
                    keys_written.append(key)
            driver.close()
            driver.quit()
            return False, keys_written
        except:
            return True, keys_written
