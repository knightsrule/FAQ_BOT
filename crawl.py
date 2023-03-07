import io
import json
import os
import re
import scrapy
from pathlib import Path
from urllib.parse import urlparse
from scrapy.selector import Selector
from urllib.parse import urlparse
from bs4 import BeautifulSoup, CData, Comment, NavigableString, Tag
from scrapy.crawler import CrawlerProcess
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from scrapy.utils.log import configure_logging
from config_parser import parse_config
import PyPDF2
from lxml import html


class MyBeautifulSoup(BeautifulSoup):
    def _all_strings(self, strip=False, types=(NavigableString, CData)):
        # verify types [ADDED]
        if hasattr(types, '__iter__'):
            types = tuple([t for t in types if isinstance(t, type)])
        if types is None:
            types = NavigableString
        if not types or not isinstance(types, (type, tuple)):
            types = (NavigableString, CData)

        for descendant in self.descendants:
            # return "a" string representation if we encounter it

            if isinstance(descendant, Tag) and descendant.name == 'a' and descendant.get('href', '') != '#':
                yield str('{} {} '.format(descendant.text, descendant.get('href', '')))

            # skip an inner text node inside "a"
            if isinstance(descendant, NavigableString) and descendant.parent.name == 'a':
                continue

            if not isinstance(descendant, types):
                continue  # default behavior [EDITED]

            if strip:
                descendant = descendant.strip()
                if len(descendant) == 0:
                    continue
            yield descendant


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
        self.BASE_URL_DETAILS = urlparse(self.BASE_URL)
        self.secPDFURL = getattr(self, 'secPDFURL', '')
        self.ifSaveHTML = getattr(self, 'ifSaveHTML', False)

        # print("in the constructor: ", self.BASE_URL, self.MAX_DEPTH)
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

    def createCleanLink(self, link_url, ifLimitDomain):
        if link_url.startswith("#") or link_url.startswith("mailto:") or link_url.startswith("tel:"):
            return link_url

        clean_link = ""
        # If the link is a URL, check if it is within the same domain
        if re.search(self.HTTP_URL_PATTERN, link_url):
            if ifLimitDomain:
                # Parse the URL and check if the domain is the same
                url_obj = urlparse(link_url)
                if url_obj.netloc == self.BASE_URL_DETAILS.netloc:
                    clean_link = link_url
            else:
                clean_link = link_url

        # If the link is not a URL, check if it is a relative link
        else:
            if link_url.startswith("/"):
                link_url = link_url[1:]

            clean_link = self.BASE_URL_DETAILS.scheme + "://" + \
                self.BASE_URL_DETAILS.netloc + "/" + link_url

            # print("old link: ", link_url, " new link: ", clean_link)
        if clean_link is not None:
            if clean_link.endswith("/"):
                clean_link = clean_link[:-1]

        return clean_link

    def get_domain_hyperlinks(self, response):

        clean_links = []

        # Find all hyperlinks on the webpage and follow them
        for link in response.xpath('//a/@href'):

            # link_url = response.urljoin(link.extract())
            link_url = link.extract()

            if link_url and not (link_url.startswith("#") or link_url.startswith("mailto:") or link_url.startswith("tel:")):

                # print(link, link_url)
                clean_link = self.createCleanLink(link_url, True)
                # print("old: ", link_url, " new: ", clean_link)

                if clean_link:
                    clean_links.append(clean_link)

        # Return the list of hyperlinks that are within the same domain
        return list(set(clean_links))

    def start_requests(self):

        if self.BASE_URL:

            # Create a directory to store the text files
            if not os.path.exists("text/"):
                os.mkdir("text/")

            if not os.path.exists("text/"+self.BASE_URL_DETAILS.netloc+"/"):
                os.mkdir("text/" + self.BASE_URL_DETAILS.netloc + "/")

            yield scrapy.Request(url=self.BASE_URL, callback=self.parse, meta={'depth': 1})
            if self.secPDFURL:
                yield scrapy.Request(url=self.secPDFURL, callback=self.parsePDF)
        else:
            print('no base url found')

    def parsePDF(self, response, fileNameBase, ifSaveOriginal):
        # Save text from the url to a <url>.txt file

        url = response.url

        if url.endswith('/'):
            url = url[:-1]

        pdf_bytes = response.body

        if ifSaveOriginal:
            #save the content as a PDF file
            print('save PDF')
            fileName = fileNameBase +  '.pdf'
            # print("PDF file name is: ", fileName)
            # print('response length is: ', len(pdf_bytes))
            with open(fileName, "wb") as f:
                f.write(pdf_bytes)
                f.close

        #now save the text version of the file
        fileName = fileNameBase +  '.txt'
        # print("PDF file name is: ", fileName)
        # print('response length is: ', len(pdf_bytes))

        with open(fileName, "w", encoding="UTF-8") as f:

            pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_bytes))
            text = ''
            # print("Number of pages is: ", len(pdf_reader.pages))
            for i in range(len(pdf_reader.pages)):
                page = pdf_reader.pages[i]
                text += page.extract_text()
                # print("page : ", i+1, " size: ", len(page.extract_text()))

            f.write(text)

    def saveSimplifiedHTML(self, response, fileNameBase, ifSaveOriginal):

        if not fileNameBase:
            print("fileName in saveSimplifiedHTML is empty")
            return

        body = scrapy.Selector(response).xpath('//body').getall()
        # Print the header of the page
        title = response.xpath('//head/title/text()').get()

        soup = MyBeautifulSoup(''.join(body), 'html.parser')

        # Remove all comments
        for comment in soup.findAll(string=lambda text: isinstance(text, Comment)):
            comment.extract()

        for script in soup(["script", "style", "link", "meta", "symbol", "svg", "form", "footer", "button"]):
            script.extract()

        # Find all elements with class attribute
        elements_with_class = soup.find_all(class_=True)

        # Remove class attribute from each element
        for element in elements_with_class:
            del element['class']

        for tag in soup.find_all('a'):
            current_href = tag.get('href')
            if current_href and not current_href.startswith(('tel:', 'mailto:')):
                new_href = self.createCleanLink(current_href, False)
                if new_href != current_href:
                    tag['href'] = new_href
                    # print("in save html, link cleanup. old link: ",current_href, " new link: ", new_href)
                # else:
                #    print('same href')
            # else:
            #    print("no href")

        if ifSaveOriginal:
            clean_html = soup.prettify()
            with open(fileNameBase + ".html", "w", encoding="UTF-8") as f:
                f.write(clean_html)
                f.close()

        #now save the text version of the file
        self.saveTextFile(title, soup, fileNameBase)

    def saveTextFile(self, title, soup, fileNameBase):

        if not fileNameBase:
            print("file name in saveTextFile is empty")
            return

        with open(fileNameBase + ".txt", "w", encoding="UTF-8") as f:

            # Print the header of the page
            # header = response.xpath('//head').get()
            # f.write(f'Header of {response.url}:\n{header}\n\n')

            # Print the header of the page
            if title:
                f.write(f'{title}\n\n')

            # Print the footer of the page
            # footer = response.xpath('//footer').get()
            # f.write(f'Footer of {response.url}:\n{footer}\n\n')

            # Print the plain text version of the body of the page
            # body_text = ''.join([text.strip() for text in body])
            body_text = self.remove_newlines(soup.get_text())
            # body_text = ''.join(response.selector.select(
            #    "//body//text()").extract()).strip()

            f.write(body_text)

    def parse(self, response):

        url = response.url
        depth = response.meta.get('depth', 0)
        if depth > self.MAX_DEPTH:
            print(url, ' at depth ', depth, " is too deep")
            return

        print("processing: ", url)
        content_type = response.headers.get('Content-Type').decode('utf-8')
        print(f'Content type: {content_type}')    
        
        if url.endswith('/'):
            url = url[:-1]

        url_info = urlparse(url)
        if url_info.path:
            file_info = os.path.splitext(url_info.path)
            fileName = file_info[0]
            if fileName.startswith("/"):
                fileName = fileName[1:]
            fileName = fileName.replace("/", "_")

            fileNameBase = 'text/' + \
                self.BASE_URL_DETAILS.netloc + '/' + fileName
        else:
            fileNameBase = 'text/' + self.BASE_URL_DETAILS.netloc + '/home'

        if "pdf" in content_type:
            self.parsePDF(response, fileNameBase, True)
        elif "html" in content_type:
            self.saveSimplifiedHTML(response, fileNameBase, True)

            # if the current page is not deep enough in the depth hierarchy, download more content
            if depth < self.MAX_DEPTH:
                # get links from the current page
                subLinks = self.get_domain_hyperlinks(response)

                # tee up new links for traversal
                for link in subLinks:
                    if link not in self.visited_links:
                        # print("New link found: ", link)
                        self.visited_links.add(link)
                        yield scrapy.Request(url=link, callback=self.parse, meta={'depth': depth + 1})
                    # else:
                    #    print("Previously visited link: ", link)


start_url, depth, log_level, secPDFURL, ifSaveHTML = parse_config()

# logging.getLogger().setLevel(log_level)
# configure_logging({'LOG_LEVEL': log_level})


# Create a new Scrapy process
process = CrawlerProcess()

# process = CrawlerProcess({
#    'USER_AGENT': 'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1)'
# })

process.crawl(SiteDownloadSpider, input='inputargument',
              url=start_url, depth=depth, secPDFURL=secPDFURL, ifSaveHTML=ifSaveHTML)

process.start()  # the script will block here until the crawling is finished
