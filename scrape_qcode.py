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


def find_click_n_wait(driver, current_xpath, next_xpath, section_num, wait_time, extra_time):
    """find element click on it and wait till it is present"""
    my_section = driver.find_elements_by_xpath(current_xpath)
    click_n_wait(next_xpath, my_section, section_num, wait_time, extra_time)

def click_n_wait(next_xpath, my_section, section_num, wait_time, extra_time):
    """click on current section and wait for next xpath to be present"""
    my_section[section_num].click()
    waiting_for_presence_of(next_xpath, wait_time, extra_time)

def waiting_for_presence_of(next_xpath, wait_time, extra_time):
    waiting = WebDriverWait(driver, wait_time).until(EC.presence_of_element_located((By.XPATH, next_xpath)))
    time.sleep(extra_time)


def q_code_main(start_links, base_loc):
    chrome_options = webdriver.ChromeOptions()
    #set download folder
    #configure multiple file download and turn off prompt
    prefs = {'download.default_directory' : base_loc,
            'profile.default_content_setting_values.automatic_downloads': 1,
            'download.prompt_for_download': 'False'}
    chrome_options.add_experimental_option('prefs', prefs)
    failed_cities = []
    my_xpath = "//div[@class='navChildren']//a"
    showall_xpath = "//a[@class='showAll']"
    high_title_xpath = "//div[@class='currentTopic']"
    low_title_xpath = "//div[@class='navTocHeading']"
    content_xpath = "//div[@class='content-fragment']"
    up_xpath = "//a[@accesskey='u']"
    for city, links in start_links:
        print(city)
        for link in links:
            driver = webdriver.Chrome('/usr/local/bin/chromedriver',options=chrome_options)
            print(link)
            driver.get(link)
            my_doc = [city]
            driver.get(link)
            # find effective date
            driver.switch_to.frame('LEFT')
            date_xpath = "//body[@class='preface']//p"
            waiting_for_presence_of(date_xpath, 3, 0.1)
            left_text = driver.find_elements_by_xpath(date_xpath)
            for p in left_text:
                if 'current' in p.text.lower():
                    my_doc.append(p.text)
            driver.switch_to.default_content()
            driver.switch_to.frame('RIGHT')
            waiting_for_presence_of(my_xpath, 3, 0.1)
            # get to start of doc
            for h_sec_num in range(len(driver.find_elements_by_xpath(my_xpath))):
                h_sections = driver.find_elements_by_xpath(my_xpath)
                print(h_sections[h_sec_num].text)
                my_doc.append(h_sections[h_sec_num].text)
                click_n_wait(my_xpath, h_sections, h_sec_num, 3, 0.1)
                for l_sec_num in range(len(driver.find_elements_by_xpath(my_xpath))):
                    try:
                        l_sections = driver.find_elements_by_xpath(my_xpath)
                        my_doc.append(l_sections[l_sec_num].text)
                        click_n_wait(showall_xpath, l_sections, l_sec_num, 3, 0.1)
                        find_click_n_wait(driver, showall_xpath, high_title_xpath, 0, 3, 0.1)
                        h_title = driver.find_elements_by_xpath(high_title_xpath)
                        my_doc.append(h_title[0].text)
                        for content, l_title in zip(driver.find_elements_by_xpath(content_xpath), driver.find_elements_by_xpath(low_title_xpath)):
                            my_doc.append(l_title.text)
                            my_doc.append(content.text)
                        up = driver.find_elements_by_xpath(up_xpath)
                        click_n_wait(my_xpath, up, 0, 3, 0.1)
                    except:
                        my_doc.append("-_-_-missing-_-_-")
                        missing_sections += 1
                        driver.get(link)
                        driver.switch_to.frame('RIGHT')
                        find_click_n_wait(driver, my_xpath, my_xpath, h_sec_num, 3, 0.1)
                find_click_n_wait(driver, up_xpath, my_xpath, 0, 3, 0.1)
            if "-_-_-missing-_-_-" in my_doc:
                failed_cities.append([city, [link]])
                print(f"missed {missing_sections} sections")
            # save file to path
            path = make_path(base_loc, city.replace(" ", ""), my_doc[1])
            with open(f"{path}/{city}.txt", "w") as text_file:
                text_file.write('\n'.join(my_doc))
            print(f"{path}/{city}.txt")
            print("-"*5)
        driver.close()
        driver.quit()
