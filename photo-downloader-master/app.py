from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import requests
import datetime
import time
import re
import os
import shutil
import json
from flask import Flask, request, jsonify
from flask_cors import CORS
import logging

# Global vars
start_time = None
current_task = 'idle'
DOWNLOAD_TEMP_FILE = "to_download.txt"
to_download = []
downloaded = set()
log_progress = []
LOG_NAME = "output.log"
logging.basicConfig(filename=LOG_NAME, level=logging.INFO,
        format=('%(filename)s: ' 
                '%(asctime)s: '   
                '%(levelname)s: '
                '%(funcName)s(): '
                '%(lineno)d:\t'
                '%(message)s'))
login_page = "https://secure.smugmug.com/login"

def retrieve(root_url, password, username=None, headless=False):
    """
    Retrieve all pictures below a root url
    """
    logging.info(f"retrieve {root_url}")
    global to_download
    global login_page

    # init & auth
    chrome_options = Options()
    if headless:
        chrome_options.add_argument("--headless")
    driver = webdriver.Chrome(ChromeDriverManager().install(), options=chrome_options)
    
    # authenticate before navigating to gallery
    driver.get(login_page)
    authenticate(driver, password, username=username)
    
    time.sleep(2)
    driver.get(root_url)
    time.sleep(2)
    to_download = []
    get_all_urls_and_save_alt(driver, root_url, [], to_download)


def generate_original_url_from_link(l):
    """
    Take a link and sub in the O suffix to redirect to original size
    """
    logging.info(f"generate_original_url_from_link for {l}")
    if len(l) == 0:
        logging.error(f"ERROR! Length cannot be zero {l}")
        return l
    sizing_pattern = re.search('/[A-z]{1,2}/', l)
    if sizing_pattern is None:
        l = l.replace(l.split('/')[-2], 'O')
        return l
    sizing_pattern = sizing_pattern.group(0)
    sizing_pattern = sizing_pattern.replace('/', '')
    l = l.replace('/{}/'.format(sizing_pattern), '/O/')
    l = l.replace('-{}.'.format(sizing_pattern), '-O.')
    return l


def make_dir_and_download(link_url):
    """
    Create directory structure necessary for saving the photo and then
    proceed with the download
    :param link_url: The direct URL to the photo to download
    """
    global start_time
    global log_progress

    logging.info(f"make_dir_and_download {link_url}")

    dir_structure = link_url.split('/')
    for i in range(0, len(dir_structure)):
        if dir_structure[i][-4:] == '.com':
            remainder = dir_structure[i + 1:]
            for j in range(0, len(remainder)):
                split_match = re.search('^[0-9]{1,2}$', remainder[j])
                if split_match is not None and split_match.group(0) == remainder[j]:
                    dir_structure = dir_structure[i + 1: i + 1 + j]
                    dir_structure[-1] = dir_structure[-1] + "." + remainder[-1].split('.')[-1]  # add extension
                    new_directory = f"../downloads-{start_time}/{'/'.join(dir_structure[0:-1])}/"
                    new_file = dir_structure[-1]

                    # Create dir if not existing
                    if not os.path.exists(new_directory):
                        os.makedirs(new_directory)

                    # Download file and save it
                    resp = requests.get(link_url, stream=True) #this is returning a 404
                    # logging.info(resp.reason)
                    if resp.status_code == 200:
                        with open(new_directory + new_file, 'wb') as f:
                            shutil.copyfileobj(resp.raw, f)
                        del resp
                    else:
                        raise Exception("Non-200 response on ", link_url)

                    log_progress = log_progress[-9:] + [link_url]
                    time.sleep(0.1)  # Don't ddos
                    return
            raise Exception("Unable to determine appropriate filename for link ", link_url)


def authenticate(driver, password, username=None):
    """
    Pass auth params to webpage
    """
    logging.info("authenticate")
    try:
        if username is not None:
            if (type(username) == type([]) and username[0] is not None) or type(username) != type([]):
                    username_area = driver.find_element("name", "username")
                    username_area.clear()
                    username_area.send_keys(username)
        password_area = driver.find_element("name", "password")
        password_area.clear()
        password_area.send_keys(password)
        password_area.send_keys(Keys.RETURN)
        time.sleep(5)
    except Exception as e:
        logging.error(f"Encountered exception while authorizing: {e}")


def get_all_urls_and_save_alt(driver, root_url, visited, to_download, second_chance=False):
    """
    Scrape root folder
    """
    global downloaded

    logging.info(f"get_all_urls_and_save_alt {root_url}\tvisited: {len(visited)}\tto_download:{len(to_download)}")
    visited.append(root_url)
    if type(root_url) != type("a"):
        logging.error(f"Received root_url ({root_url}) of type ({type(root_url)})")
        return
    driver.get(root_url)

    # Quick sleep to load more shit
    sleep_interval = 3
    logging.info(f"Sleeping for {sleep_interval} sec to render all images on page")
    time.sleep(sleep_interval)

    # Verify we loaded page properly
    page_type = None
    to_visit = []
    tiles = []
    count = 0
    while len(tiles) == 0 and count < 3:
        # Check for gallery page
        tiles = driver.find_elements("xpath", '//li[contains(@class,"sm-tile-album")]')
        logging.info(f"LENGTH OF TILES ALMBUM: {len(tiles)}")
        if len(tiles) > 0:
            page_type = "gallery"
            break
        # Check for image page
        tiles = driver.find_elements("xpath", "//li[contains(@class,'tile-photo')]")
        logging.info(f"LENGTH OF TILES PHOTO: {len(tiles)}")
        if len(tiles) > 0:
            page_type = "images"
            break
        count += 1
        time.sleep(max(count * 2, 2))  # backoff sleep
        logging.info("sleeping again, didn't find anything")
    
    # Problem case
    if page_type is None:
        logging.info("page_type is None")
        if not second_chance:
            logging.info("Issue finding any content, second chancing")
            get_all_urls_and_save_alt(driver, root_url, visited, to_download, second_chance=True)
        else:
            logging.info(f"Was unable to find any pictures or galleries at this level even after second chance")
            return

    # Gallery mode - look for all sub-galleries to visit, note them in to_visit
    elif page_type == "gallery":
        logging.info("Identified a gallery")
        for t in tiles:
            if t is not None:
                link_url = driver.find_element("css selector", f"#{t.get_attribute('id')} a").get_attribute('href')
                logging.info(link_url)
                if link_url is not None and link_url not in visited:
                    to_visit.append(link_url)

    # images mode - look for all images to download
    elif page_type == "images":
        logging.info(f"Identified a list of images, tiles len {len(tiles)}")
        for t in tiles:
            if t is not None:
                img_url = t.find_element("tag name", 'img').get_attribute('src')
                if img_url not in downloaded:
                    downloaded.add(img_url)
                    make_dir_and_download(generate_original_url_from_link(img_url))
        right_button = driver.find_elements("xpath", '//a[contains(@class,"nav-right")]')
        if len(right_button) > 0:
            next_img_link = right_button[0].get_attribute("href")
            logging.info(f"Found right button, trying to retrieve URL (len={len(right_button)}) with href ({next_img_link})")
            get_all_urls_and_save_alt(driver, next_img_link, visited, to_download)

    # Iterate over all remaining to-vist links
    for v in to_visit:
        if v in downloaded or v in visited:
            continue
        else:
            logging.info("Exiting for a to_visit page")
            get_all_urls_and_save_alt(driver, v, visited, to_download)

    return

# TODO: Compress resulting downloads folder
# TODO: Test on other pages
# TODO: Download metadata + descriptive info if possible

app = Flask(__name__)
cors = CORS(app)

@app.route("/download", methods=["POST"])
def run():
    try:
        logging.info(f"running with {request.data}")
        # Setup markers
        global current_task, start_time, DOWNLOAD_TEMP_FILE, log_progress
        current_task = 'Retrieve'
        start_time = datetime.datetime.now()

        # Begin actual task
        request_json = json.loads(request.data)
        email = None if 'email' not in request_json.keys() else request_json['email']
        password = request_json['password']
        root_url = request_json['root_url']
        retrieve(root_url, password, email, headless=False)

        # Reset
        current_task = 'idle'
        start_time = None
        log_progress = []
        logging.info("Finishing up, returning successful status")
        return jsonify(success=True)
    except Exception as e:
        logging.error(f"Encountered exception {e}")
        current_task = 'error'
        return jsonify({"error": e})


@app.route("/status", methods=["GET"])
def send_status():
    global current_task, start_time, DOWNLOAD_TEMP_FILE, log_progress, to_download, downloaded

    current_task_desc = None
    if current_task == 'Retrieve':
        current_task_desc = f"Retrieving URLs of all photos present and downloading. So far, {len(downloaded)} found & saved."
    elif current_task == 'Download':
        for root, dirs, files in os.walk("./downloads"):
            current_task_desc = f"Downloading photos [{len(files)} / {len(to_download)}]"

    return jsonify({
        'current_task': current_task,
        'current_task_desc': current_task_desc,
        'time_elapsed': None if start_time is None else str(datetime.datetime.now() - start_time),
        'log_progress': log_progress
    })


if __name__ == "__main__":
    print("To run this, enter 'flask run'")
    url = "https://www.smugmug.com/app/organize/Caviar/Library/AIRPORTSFBOSPLANES/Airplane-Legacy-Movie-Ranch-at-Grumman"
    pw = "gildaradner"
    user = "locationscoutingny@gmail.com"

    driver = webdriver.Chrome(ChromeDriverManager().install())
    driver.get(url)
    authenticate(driver, pw, user)
    time.sleep(5)
    tiles = driver.find_elements("xpath", '//*[@class="sm-tiles-list"]')
    tiles = tiles[0].find_elements_by_tag_name("li")
    print(len(tiles))












