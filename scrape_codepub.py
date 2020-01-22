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
            print("--> found the plus button")
        # return to the general case
        if len(driver.find_elements_by_xpath(my_xpath)) < 2:
            my_xpath = "//p/input[@type='checkbox']"
    # too general, must be more specific
    elif len(driver.find_elements_by_xpath(my_xpath)) > 80:
        my_xpath = "//form/p/input[@type='checkbox']"
    # check all the boxes
    missed_checks = []
    for checkbox in driver.find_elements_by_xpath(my_xpath):
        time.sleep(random.uniform(s_sleep,l_sleep))
        try:
            checkbox.location_once_scrolled_into_view
            checkbox.click()
        except:
            missed_checks.append(checkbox)
    print(f"missed: {len(missed_checks)}")
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
    time.sleep(4)
    # click the submit button
    submit_btn = driver.find_element_by_id("saveAsSubmit")
    submit_btn.click()
    return driver


def make_path(base_loc, city, my_date):
    try:
        match = re.search(r'passed\s(.+?)\.', my_date)
        date = datetime.strptime(match.group(1), '%B %d, %Y').date()
    except:
        match = re.search(r'Ordinance\s(.+?)\sand', my_date)
        date = datetime.strptime(match.group(1), '%Y-%m').date()
    num_date = date.strftime('%m-%d-%y')
    path = f"{base_loc}/{city}/{num_date}"
    try:
        os.makedirs(path, exist_ok=True)
    except OSError:
        if not os.path.isdir(path):
            raise
    return path


def get_effective_date(driver):
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


def code_pub_main(start_links, base_loc):
    chrome_options = webdriver.ChromeOptions()
    #set download folder
    #configure multiple file download and turn off prompt
    prefs = {'download.default_directory' : base_loc,
            'profile.default_content_setting_values.automatic_downloads': 1,
            'download.prompt_for_download': 'False'}
    chrome_options.add_experimental_option('prefs', prefs)
    failed_cities = []
    for city, links in start_links:
        print(city)
        for link in links:
            try:
                driver = webdriver.Chrome('/usr/local/bin/chromedriver',options=chrome_options)
                print(link)
                driver.get(link)
                # find effective date
                my_date = get_effective_date(driver)
                # find and click all necessary checkboxes
                driver = handle_checkboxes(driver, 0.4, 0.5)
                # save the document
                driver = save_doc(driver)
                # waits for files to download
                paths = WebDriverWait(driver, 60, 1).until(every_downloads_chrome)
                print(paths)
                new_path = make_path(base_loc, city, my_date[0])
                city = city.replace(" ", "")
                os.rename(base_loc+"/"+city+".rtf", new_path+"/"+city+".rtf")
                print(new_path+"/"+city+".rtf")
                driver.close()
                driver.quit()
            except:
                print("failed! try again later")
                failed_cities.append([city, [link]])
            print("-"*5)
    print("-"*10)
    for x in failed_cities:
        print(x)
    return failed_cities
