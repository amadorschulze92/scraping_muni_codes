from selenium import webdriver
from time import sleep
import os
from datetime import datetime

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import sys
import getpass

user = getpass.getuser()
sys.dont_write_bytecode = True

# Select one of the following paths:

# for DataViz team members
sys.path.insert(0, "../Utility Code/")

# # for all other teams with access to the Utility Code folder
# sys.path.insert(0, '/Users/{}/Box/Utility Code'.format(user))

from utils_io import *


def generate_municode_links():
    city_county = 'Alameda County,Contra Costa County,Marin County,Napa County,City and County of San Francisco,San Mateo County,' \
                  'Santa Clara County,' \
                  'Solano County,Sonoma County,Alameda,Albany,Berkeley,Dublin,Emeryville,Fremont,Hayward,Livermore,Newark,Oakland,Piedmont,' \
                  'Pleasanton,' \
                  'San Leandro,Union City,Antioch,Brentwood,Clayton,Concord,Danville,El Cerrito,Hercules,Lafayette,Martinez,Moraga,Oakley,Orinda,' \
                  'Pinole,' \
                  'Pittsburg,Pleasant Hill,Richmond,San Pablo,San Ramon,Walnut Creek,Belvedere,Fairfax,Larkspur,Mill Valley,Novato,Ross,' \
                  'San Anselmo,' \
                  'San Rafael,Sausalito,Tiburon,American Canyon,Calistoga,Napa,St. Helena,Yountville,Atherton,Belmont,Brisbane,Burlingame,' \
                  'Colma,Daly City,East Palo Alto,Foster City,Half Moon Bay,Hillsborough,Menlo Park,Millbrae,Pacifica,Portola Valley,Redwood City,' \
                  'San Bruno,San Carlos,San Mateo,South San Francisco,Woodside,Campbell,Cupertino,Gilroy,Los Altos,Los Altos Hills,Los Gatos,' \
                  'Milpitas,' \
                  'Monte Sereno,Morgan Hill,Mountain View,Palo Alto,San Jose,Santa Clara,Saratoga,Sunnyvale,Benicia,Dixon,Fairfield,Rio Vista,' \
                  'Suisun City,Vacaville,Vallejo,Cloverdale,Cotati,Healdsburg,Petaluma,Rohnert Park,Santa Rosa,Sebastopol,Sonoma,Windsor'

    city_county = city_county.split(",")

    driver = webdriver.Chrome('/Users/kjafshar/dev/MTC-Work/chromeDRIVER')
    driver.get('https://library.municode.com/ca')

    element = WebDriverWait(driver, 20) \
        .until(EC.element_to_be_clickable((By.CSS_SELECTOR, "li[ng-repeat='client in letterGroup.clients']")))

    ca_links = driver.find_elements_by_tag_name("li")

    # filter to desired municipalities
    muni_links = [link for link in ca_links if link.text in city_county]

    muni_links = [(link.text, link.find_element_by_tag_name("a").get_attribute("href")) for link in muni_links]

    driver.quit()

    return muni_links



def extract_text(driver):
    filler_text = "\nSHARE LINK TO SECTION\nPRINT SECTION\nDOWNLOAD (DOCX) OF SECTIONS\nEMAIL SECTION"
    element = WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.CSS_SELECTOR, "div[ng-switch-when='CHUNKS']")))
    doc = driver.find_element_by_css_selector('ul[class="chunks list-unstyled small-padding"]').text
    doc = doc.replace(filler_text, '')
    return doc


def toc_crawler(driver):
    smalltoc = driver.find_elements_by_css_selector("li[depth='-1']")
    l_2_doc = []

    for sub_chap in smalltoc:
        sub_chap.click()
        sleep(1)
        if driver.find_elements_by_css_selector("div[ng-switch-when='CHUNKS']"):
            l_2_doc.append(extract_text(driver))
        elif driver.find_elements_by_css_selector("div[ng-switch-when='TOC']"):
            level_3_doc = []
            tinytoc = sub_chap.find_elements_by_css_selector("li[depth='-1']")
            for subsub_chap in tinytoc:
                sleep(1)
                subsub_chap.click()
                level_3_doc.append(extract_text(driver))
            l_2_doc.append("\n".join(level_3_doc))

    return "\n".join(l_2_doc)


def page_crawler(driver, s3_bucket, s3_path, s3_table, base_loc, muni, update_date):
    element = WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.CSS_SELECTOR, "section[id='toc']")))
    toc = [link for link in driver.find_element_by_css_selector("section[id='toc']").find_elements_by_tag_name("li")]
    for chap in toc[:5]:
        title = chap.text
        print(title)
        chap.click()

        sleep(2)

        if driver.find_elements_by_css_selector("div[ng-switch-when='CHUNKS']"):

            s3_file_writer(s3_bucket, s3_path, s3_table, base_loc, muni, update_date, title, extract_text(driver))

        elif driver.find_elements_by_css_selector("div[ng-switch-when='TOC']"):

            s3_file_writer(s3_bucket, s3_path, s3_table, base_loc, muni, update_date, title, toc_crawler(driver))

        else:

            print(f'{muni}-{title} failed')

        close_button = driver.find_elements_by_css_selector('i[class="fa-fw fa fa-chevron-down"]')
        if close_button:
            close_button[0].click()




def check_for_s3_delta(muni, title, text, s3_table):
    return True


def s3_file_writer(s3_bucket, s3_path, s3_table, base_loc, muni, update_date, title, text):
    """
    This function will combine downloaded docs into a single txt

    :param base_loc: path to download folder
    :param output_dir: path to output directory
    :param i: given index of doc
    :param muni: municipality name
    :param update_date: data municode updated
    :param names: list of article names for given muni
    :return: nothing
    """

    s3_key = (s3_path +
              muni + "/" +
              update_date + '/' +
              title + ".txt")

    filename = base_loc + title + '.txt'

    if check_for_s3_delta(muni, title, text, s3_table):
        with open(filename, 'w') as f:
            f.write(text)

        copy_file_to_s3(filename, s3_bucket, s3_key)
        # write to s3
        #except:
        #print(f'file issue for {filename}')
        #print('')
        # os.remove(filename)
        print('file write complete')
        print('')
    else:
        print("doc hasn't changed")
        print('')


    # remove any docs left in download folder


def municode_scraper(s3_bucket, s3_path, s3_table, base_loc, url):

    driver = webdriver.Chrome('/Users/kjafshar/dev/MTC-Work/chromeDRIVER')
    driver.get(url)

    sleep(1)

    # check municipality name
    muni = driver.current_url.split('/')[4]
    print(muni)
    print('')
    sleep(3)
    # check for a division first before exposing docs

    try:
        update_date = driver.find_element_by_class_name("product-date").text  # update data only visible on actual code page, works as a check
    except:
        x = ([link for link in driver.find_elements_by_tag_name("li")
              if "municipal" in link.text.lower() or "ordinance" in link.text.lower()])[0]

        x.find_elements_by_tag_name("a")[0].click()
        div_page = True
        sleep(1)
        update_date = driver.find_element_by_class_name("product-date").text

    # format update date

    update_date = update_date.split(' ')[-3:]

    update_date = datetime.strptime("-".join(update_date), '%B-%d,-%Y').date()

    update_date = update_date.strftime('%m-%d-%y')

    # check for popup-window

    try:
        popup_button = WebDriverWait(driver, 5) \
    .until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button[class='hopscotch-bubble-close hopscotch-close']")))

        popup_button.click()
    except:
        pass

    try:
        page_crawler(driver, s3_bucket, s3_path, s3_table, base_loc, muni, update_date)

        # create named files

        print(f'finished crawling for {muni}')

        # if page had division early on it two backs

        driver.quit()

    except:

        driver.quit()

        return "failed"

    driver.quit()