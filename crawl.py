from collections import deque
import json
from os import path
import os
import re
from urllib.parse import urlparse
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

# Regex pattern to match a URL
HTTP_URL_PATTERN = r'^http[s]*://.+'


configFile = open("config.json", "r")
config = json.loads(configFile.read())
configFile.close()

# Define root domain to crawl
full_url = config["base_url"]

if config['max_level']:
    MAX_LEVEL = config["max_level"]
else:
    MAX_LEVEL = 50

# Parse the URL and get the domain
local_domain = urlparse(full_url).netloc

# Function to get html of a URL


def fetch_url_selenium(driver, url):

    driver.get(url)
    html = driver.page_source
    return html

################################################################################
# Step 2
################################################################################

# Function to get the hyperlinks from a URL


def get_hyperlinks(soup):

    # Open the URL and read the HTML
    alllinks = soup.find_all('a')
    cleanLinks = []
    for link in alllinks:

        if link.has_attr('href'):
            cleanLinks.append(link["href"])

    return cleanLinks


################################################################################
# Step 3
################################################################################

# Function to get the hyperlinks from a URL that are within the same domain


def get_domain_hyperlinks(soup):
    clean_links = []
    for link in set(get_hyperlinks(soup)):
        clean_link = None

        # If the link is a URL, check if it is within the same domain
        if re.search(HTTP_URL_PATTERN, link):
            # Parse the URL and check if the domain is the same
            url_obj = urlparse(link)
            if url_obj.netloc == local_domain:
                clean_link = link

        # If the link is not a URL, check if it is a relative link
        else:
            if link.startswith("/"):
                link = link[1:]
            elif link.startswith("#") or link.startswith("mailto:"):
                continue
            clean_link = "https://" + local_domain + "/" + link

        if clean_link is not None:
            if clean_link.endswith("/"):
                clean_link = clean_link[:-1]
            clean_links.append(clean_link)

    # Return the list of hyperlinks that are within the same domain
    return list(set(clean_links))


################################################################################
# Step 4
################################################################################

def crawl(url):

    # Create a queue to store the URLs to crawl
    queue = deque([{"url": url, "level": 1}])

    # Create a set to store the URLs that have already been seen (no duplicates)
    seen = set([url])

    # Create a directory to store the text files
    if not os.path.exists("text/"):
        os.mkdir("text/")

    if not os.path.exists("text/"+local_domain+"/"):
        os.mkdir("text/" + local_domain + "/")

    # Create a directory to store the csv files
    if not os.path.exists("processed"):
        os.mkdir("processed")

    if not os.path.exists("processed/"+local_domain+"/"):
        os.mkdir("processed/" + local_domain + "/")

    options = Options()
    options.add_argument("--headless")
    driver = webdriver.Chrome(options=options)

    # While the queue is not empty, continue crawling
    while queue:

        # Get the next URL from the queue
        entry = queue.pop()
        url = entry['url']
        level = entry['level']

        if level <= MAX_LEVEL:

            # for debugging and to see the progress
            print('processing: ' + url + ' at level ' + str(level))

            html = fetch_url_selenium(driver, url)
            # Get the text from the URL using BeautifulSoup
            soup = BeautifulSoup(html, "html.parser")

            # Get the text but remove the tags
            text = soup.get_text()

            # Save text from the url to a <url>.txt file
            with open('text/'+local_domain+'/'+url[8:].replace("/", "_") + ".txt", "w", encoding="UTF-8") as f:

                # If the crawler gets to a page that requires JavaScript, it will stop the crawl
                if ("You need to enable JavaScript to run this app." in text):
                    print("Unable to parse page " + url +
                          " due to JavaScript being required")

                # Otherwise, write the text to the file in the text directory
                f.write(text)

            # Get the hyperlinks from the URL and add them to the queue
            for link in get_domain_hyperlinks(soup):
                if link not in seen:
                    queue.append({'url': link, 'level': level + 1})
                    seen.add(link)
        else:
            print(url + ' at level ' + str(level) + ' is too deep')

    # terminate the selenium driver
    driver.quit()


crawl(full_url)
