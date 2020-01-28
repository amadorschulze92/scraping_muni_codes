from selenium import webdriver
from time import sleep
import os
import shutil
import glob
import textract


def doc_downloader(driver, output_dir, download_path, muni, update_date,  names, last_box):
    """
    This function takes adriver object and a final index, then navigates
    to the download tab and downloads 1-last_box docs in groups of n to avoid download limits

    :param driver: driver object created in municode_scraper
    :param download_path: path to download folder
    :param output_dir: path to output directory
    :param muni: municipality
    :param update_date: date the page was updated
    :param names: list of document names
    :param last_box: index of last unique doc for muni
    :return: nothing
    """

    [button for button in driver.find_elements_by_tag_name("button") if button.text.lower() == "close"][0].click()
    for i in range(last_box):

        sleep(2)

        # identify doc download button to open download tab

        [link for link in driver.find_elements_by_tag_name("a") if "download" in link.text.lower()][0].click()
        time = 0
        x = [link for link in driver.find_elements_by_class_name("expToc-selector")][0:last_box]
        success = False
        while not success and time <= 20:
            try:
                x[0].click()
                success = True
            except:
                sleep(1)
                time += 1
                x = [link for link in driver.find_elements_by_class_name("expToc-selector")][0:last_box]

        x = x[i]
        print(f'{muni} - {x.text}')
        x.click()

        sleep(2)

        # Click download button for docs

        b = [button for button in driver.find_elements_by_tag_name("button") if button.text.lower() == "download"]

        sleep(2)

        b[0].click()

        # check to see if downloads complete

        print('waiting for dl')

        time = 0
        while len(glob.glob(download_path + '/' + '*.doc')) == 0 and time < 360:
            sleep(3)
            time += 3
        assert len(glob.glob(download_path + '/' + '*.doc')) == 1, "dl time out"
        print('dl complete')
        print(f'took {time} seconds')

        # attempt to close download tab if is open

        try:
            [button for button in driver.find_elements_by_tag_name("button") if button.text.lower() == "close"][0].click()
        except:
            pass

        # call file writer to convert word doc into named txt file

        file_writer(download_path, output_dir, i, muni, update_date, names)


def file_writer(download_path, output_dir, i, muni, update_date, names):
    """
    This function will combine downloaded docs into a single txt

    :param download_path: path to download folder
    :param output_dir: path to output directory
    :param i: given index of doc
    :param muni: municipality name
    :param update_date: data municode updated
    :param names: list of article names for given muni
    :return: nothing
    """

    city_output = output_dir + muni + '/'
    time_output = city_output + update_date + '/'
    doc = glob.glob(download_path + '/' + '*.doc')[0]
    # check to see if muni exists in results
    # if not make a dir for the muni

    if city_output not in glob.glob(output_dir + '*/'):
        os.mkdir(city_output)

    # write file inside muni/update_date

    if time_output not in glob.glob(output_dir + '*/*/'):
        os.mkdir(time_output)

    filename = time_output + names[i] + '.txt'
    try:
        """
        check redshift for most recent example of doc, extract text and compare
        there may be issues in when update date changes
        """


        # text = str(textract.process(doc))
        # if text diffs from previous text:
        # with open(filename, 'w') as f:
        #       f.write(text)

        if filename not in glob.glob(time_output + '*.txt'):
            text = str(textract.process(doc))

            with open(filename, 'w') as f:
                f.write(text)

            # move downloads
            shutil.move(doc, filename[:-4] + ".doc")

            print('file write complete')
            print('')
        else:
            print('doc already exists')
            print('')
    except:
        print(f'file issue for {filename}')
        print('')

    # remove any docs left in download folder

    dls = glob.glob(download_path + '/' + '*.doc')

    for doc in dls:
        os.remove(doc)


def municode_scraper(base_loc, spec_ind=None):

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
    # home_folder = '/Users/kjafshar/Documents/'
    download_path = base_loc + 'test_folder/'
    output_dir = download_path + 'results/'

    if download_path not in glob.glob(base_loc + '*/'):
        os.mkdir(download_path)

    if output_dir not in glob.glob(download_path + '/*/'):
        os.mkdir(output_dir)

    # enables setting of download folder

    chrome_options = webdriver.ChromeOptions()
    prefs = {'download.default_directory': download_path,
             'profile.default_content_setting_values.automatic_downloads': 1,
             'download.prompt_for_download': 'False'}

    # configure multiple file download

    chrome_options.add_experimental_option('prefs', prefs)
    chrome_options.add_argument('--no-proxy-server')

    driver = webdriver.Chrome('chromedriver', options=chrome_options)
    driver.get('https://library.municode.com/ca')

    sleep(5)

    ca_links_stale = driver.find_elements_by_tag_name("li")
    muni_links_stale = [link for link in ca_links_stale if link.text in city_county]
    muni_names = [link.text for link in muni_links_stale]
    z = len(muni_names)

    if spec_ind:
        x = spec_ind
    else:
        x = range(z)

    # create set for potential failed values

    failed = set()

    # attempt to crawl for given muni, if any failure occurs delete unconverted docs and open a new driver at the muni listing page

    for i in x:
        try:
            div_page = False

            # first gather fresh municipalities links
            ca_links = driver.find_elements_by_tag_name("li")

            # filter to desired municipalities
            muni_links = [link for link in ca_links if link.text in city_county]

            # enter municipality page
            muni_links[i].click()
            # allow page to load
            sleep(3)

            # check municipality name
            muni = driver.current_url.split('/')[4]
            print(i, muni)
            print('')

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
            update_date = datetime.strptime("-".join(update_date), '%B-%d-%Y').date()
            update_date = update_date.strftime('%m-%d-%y')

            # check for popup-window
            sleep(1)
            popup_button = [button for button in driver.find_elements_by_tag_name("button") if button.text.lower() == 'close']
            if popup_button:
                popup_button[0].click()

            # need to click on a doc first to expose download button
            base_doc = [link for link in driver.find_element_by_css_selector("section[id='toc']").find_elements_by_tag_name("li")]
            base_doc[0].click()
            sleep(2)
            [link for link in driver.find_elements_by_tag_name("a") if "download" in link.text.lower()][0].click()
            # wait for download tab to load
            sleep(20)

            # determine where list of unique docs ends

            names = [link.text.lower() for link in driver.find_elements_by_class_name("expToc-selector")]
            last_box = 0
            for j, name in enumerate(names):
                if name in names[:j]:
                    last_box = j-1
                    break

            if last_box == 0:
                last_box = len(names)

            # download docs; last_box is end index for files, n is group size

            doc_downloader(driver, output_dir, download_path, muni, update_date,  names, last_box)

            # create named files

            print(f'finished files for {muni}')

            # if page had division early on it two backs

            if div_page:
                driver.back()
            driver.back()
            driver.back()
        except:
            print(f'{muni_names[i]} failed')
            print('')

            failed.add(i)
            dls = glob.glob(download_path + '/' + '*.doc')

            for doc in dls:
                os.remove(doc)
            driver.quit()
            driver = webdriver.Chrome('chromedriver', options=chrome_options)
            driver.get('https://library.municode.com/ca')

            sleep(2)

    driver.quit()
    return list(failed)
