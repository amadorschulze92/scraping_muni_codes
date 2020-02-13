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


def every_downloads_chrome(driver):
    """return path of downloaded file
    """
    if not driver.current_url.startswith("chrome://downloads"):
        driver.get("chrome://downloads/")
    return driver.execute_script("""
        var items = downloads.Manager.get().items_;
        if (items.every(e => e.state === "COMPLETE"))
            return items.map(e => e.fileUrl || e.file_url);
        """)


def handle_checkboxes(driver, s_sleep, l_sleep):
    """ find all checkboxes related to municipal codes and click them so we can
    save entire document.
    """
    my_xpath = "//p/input[@type='checkbox']"
    # are checkboxes in another frame
    if len(driver.find_elements_by_xpath(my_xpath)) < 2:
        driver.switch_to.frame('toc')
        my_xpath = "//form/div/p/input[@type='checkbox']"
        plus_xpath = "//form/div/p/span[@id='spanmuni']"
        # are checkboxes hidden by expanded list
        if len(driver.find_elements_by_xpath(plus_xpath)) >= 1:
            for button in driver.find_elements_by_xpath(plus_xpath):
                button.click()
        # return to the general case
        if len(driver.find_elements_by_xpath(my_xpath)) < 2:
            my_xpath = "//p/input[@type='checkbox']"
    # too general, must be more specific
    elif len(driver.find_elements_by_xpath(my_xpath)) > 80:
        my_xpath = "//form/p/input[@type='checkbox']"
    # check all the boxes
    for checkbox in driver.find_elements_by_xpath(my_xpath):
        time.sleep(random.uniform(s_sleep,l_sleep))
        try:
            checkbox.location_once_scrolled_into_view
            checkbox.click()
        except:
            missed_checks.append(checkbox)
    return driver


def save_doc(driver):
    """ save the document then switch to the pop up window and download the
    document
    """
    # prep to switch windows
    window_before = driver.window_handles[0]
    # click the print button
    print_btn = driver.find_element_by_id("printSubmit")
    print_btn.click()
    # add popup driver and switch windows
    window_after = driver.window_handles[1]
    driver.switch_to.window(window_after)
    # wait for page to load
    element = WebDriverWait(driver, 180).until(EC.presence_of_element_located((By.ID, "saveAsSubmit")))
    time.sleep(1)
    #change doc type
    dropdown = driver.find_element_by_xpath("//option[@name='TEXT']")
    dropdown.click()
    time.sleep(2)
    # click the submit button
    submit_btn = driver.find_element_by_id("saveAsSubmit")
    submit_btn.click()
    return driver


def get_update_date(driver):
    my_date = []
    date_xpath = "//*[@id='pgFooter']"
    switch_date_xpath = "//p"
    try:
        driver.switch_to.frame("doc")
        driver.switch_to.frame("pgFooter")
        eff_date = driver.find_elements_by_xpath(switch_date_xpath)
    except:
        driver.switch_to.default_content()
        eff_date = driver.find_elements_by_xpath(date_xpath)
    for p in eff_date:
        if 'current' in p.text.lower():
            my_date.append(p.text)
    driver.switch_to.default_content()
    return my_date


def downloads_done(path, iterations):
    for i in range(iterations):
        if os.path.isfile(path):
            return path
        else:
            time.sleep(5)
    print("failed")


def split_lvl2_docs(new_path):
    with open(f"{new_path}", "r") as f:
        text_file = f.read()
    lines = text_file.strip().split("\n")
    lvl2_docs = {}
    lvl2_start = 0
    lvl2_end = 0
    for line_num, li in enumerate(lines):
        if re.search('[TtIiLlEe]{5,}+\s\d+\s[A-Z\s\(\)]{4,}', li):
            lvl2_end = line_num
            lvl2_docs[lines[lvl2_start]] = '\n'.join(lines[lvl2_start:lvl2_end])
            lvl2_start = line_num
    lvl2_docs[lines[lvl2_start]] = '\n'.join(lines[lvl2_start:])
    return lvl2_docs


def code_pub_main(s3_bucket, s3_path, rs_table, base_loc, start_link):
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
    failed_cities = []
    city = start_link[0]
    links = start_link[1]
    print(city)
    for link in links:
        try:
            driver = webdriver.Chrome(f'{cwd}/chromedriver', chrome_options=chrome_options)
            print(link)
            driver.get(link)
            # find update date
            messy_date = get_update_date(driver)
            # find and click all necessary checkboxes
            driver = handle_checkboxes(driver, 0.4, 0.5)
            # save the document
            driver = save_doc(driver)
            update_date = scraper_tools.extract_date(messy_date)
            # puts file in right folder and waits for files to download
            old_path = base_loc+city+".txt"
            new_path = downloads_done(old_path, 36)
            #path = scraper_tools.make_path(base_loc, city, update_date)
            path = scraper_tools.make_path(base_loc, city, update_date)
            new_path = path+city+".txt"
            os.rename(old_path, new_path)
            lvl2_docs = split_lvl2_docs(new_path)
            for lvl2_header, lvl2_text in lvl2_docs.items():
                scraper_tools.s3_file_writer(s3_bucket, s3_path, base_loc, city, update_date, lvl2_header, lvl2_text)
            driver.close()
            driver.quit()
            return (False)
        except:
            return (True)
