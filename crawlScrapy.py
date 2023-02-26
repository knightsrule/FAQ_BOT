import json
import os
import re
import scrapy
from pathlib import Path
from urllib.parse import urlparse
from scrapy.selector import Selector
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from scrapy.crawler import CrawlerProcess
import argparse
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from scrapy.utils.log import configure_logging
import logging
from config_parser import parse_config


class SiteDownloadSpider(scrapy.Spider):
    name = "download"
    MAX_DEPTH = 3
    BASE_URL = ''

    # Regex pattern to match a URL
    HTTP_URL_PATTERN = r'^http[s]*://.+'

    def __init__(self, *args, **kwargs):
        super(SiteDownloadSpider, self).__init__(*args, **kwargs)

        self.MAX_DEPTH = int(getattr(self, 'depth', 3))
        self.BASE_URL = getattr(self, 'url', '')

        print("in the constructor: ", self.BASE_URL, self.MAX_DEPTH)
        self.visited_links = set()

    # replace all occurences of src string in text with dest
    def replaceAll(self, text, src, dest):
        while src in text:
            text = text.replace(src, dest)

        return text

    def remove_newlines(self, text):

        text = text.strip()
        text = text.replace('\r', '')
        text = text.replace('\t', ' ')

        text = self.replaceAll(text, '\n\n', '\n')
        text = self.replaceAll(text, '  ', ' ')

        return text

    def get_domain_hyperlinks(self, response, root_domain):

        clean_links = []

        # Find all hyperlinks on the webpage and follow them
        for link in response.xpath('//a/@href'):

            # link_url = response.urljoin(link.extract())
            link_url = link.extract()
            # print(link, link_url)
            clean_link = None

            # If the link is a URL, check if it is within the same domain
            if re.search(self.HTTP_URL_PATTERN, link_url):
                # Parse the URL and check if the domain is the same
                url_obj = urlparse(link_url)
                if url_obj.netloc == root_domain:
                    clean_link = link_url

            # If the link is not a URL, check if it is a relative link
            else:
                if link_url.startswith("/"):
                    link_url = link_url[1:]
                elif link_url.startswith("#") or link_url.startswith("mailto:") or link_url.startswith("tel:"):
                    continue
                clean_link = "https://" + root_domain + "/" + link_url

            if clean_link is not None:
                if clean_link.endswith("/"):
                    clean_link = clean_link[:-1]
                clean_links.append(clean_link)

        # Return the list of hyperlinks that are within the same domain
        return list(set(clean_links))

    def start_requests(self):

        if self.BASE_URL:
            # Define root domain to crawl
            full_url = self.BASE_URL
            # Parse the URL and get the domain
            local_domain = urlparse(full_url).netloc

            # Create a directory to store the text files
            if not os.path.exists("text/"):
                os.mkdir("text/")

            if not os.path.exists("text/"+local_domain+"/"):
                os.mkdir("text/" + local_domain + "/")

            yield scrapy.Request(url=full_url, callback=self.parse, meta={'depth': 1, 'base_url': full_url})
        else:
            print('no base url found')

    def parse(self, response):
        # if response.url in self.visited_links:
        #    return
        # else:
        #    self.visited_links.add(response.url)

        base_url = response.meta.get('base_url', response.url)
        base_domain = urlparse(base_url).netloc
        url = response.url

        if url.endswith('/'):
            url = url[:-1]

        depth = response.meta.get('depth', 0)
        if depth > self.MAX_DEPTH:
            print(url, ' at depth ', depth, " is too deep")
            return
        else:
            print("processing: ", url)

        # Save html from the url to a <url>.html file
        # with open('text/'+base_domain+'/'+url[8:].replace("/", "_") + ".html", "w", encoding="UTF-8") as f:
        #    f.write(response.body.decode("utf-8"))

        # Save text from the url to a <url>.txt file
        with open('text/'+base_domain+'/'+url[8:].replace("/", "_") + ".txt", "w", encoding="UTF-8") as f:

            # Print the header of the page
            # header = response.xpath('//head').get()
            # f.write(f'Header of {response.url}:\n{header}\n\n')

            # Print the header of the page
            title = response.xpath('//head/title/text()').get()
            f.write(f'{title}\n\n')

            # Print the footer of the page
            # footer = response.xpath('//footer').get()
            # f.write(f'Footer of {response.url}:\n{footer}\n\n')

            # Print the plain text version of the body of the page
            body = scrapy.Selector(response).xpath('//body').getall()
            soup = BeautifulSoup(''.join(body), 'html.parser')
            # body_text = ''.join([text.strip() for text in body])
            body_text = self.remove_newlines(soup.get_text())
            # body_text = ''.join(response.selector.select(
            #    "//body//text()").extract()).strip()

            f.write(body_text)

        # get links from the current page
        subLinks = self.get_domain_hyperlinks(response, base_domain)

        # tee up new links for traversal
        for link in subLinks:
            if link not in self.visited_links:
                print("New link found: ", link)
                self.visited_links.add(link)
                yield scrapy.Request(url=link, callback=self.parse, meta={'depth': depth + 1, 'base_url': base_url})
            else:
                print("Previously visited link: ", link)


start_url, depth, log_level = parse_config()

# logging.getLogger().setLevel(log_level)
# configure_logging({'LOG_LEVEL': log_level})


# Create a new Scrapy process
# process = CrawlerProcess()

# process = CrawlerProcess({
#    'USER_AGENT': 'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1)'
# })

# process.crawl(SiteDownloadSpider, input='inputargument', url=start_url, depth=depth)

# process.start()  # the script will block here until the crawling is finished
