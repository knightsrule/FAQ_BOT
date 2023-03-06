from bs4 import BeautifulSoup, NavigableString, CData, Tag
import io
import json
import os
import re
from pathlib import Path
from urllib.parse import urlparse
from bs4 import BeautifulSoup, Comment
from config_parser import parse_config

setPrint = {"h1", "h2", "h3", "h4", "h5", "h6",
            "p", "li", "a", "span", "em", "strong", "u", "sub", "small", "address"}
setContainers = {"main", "label", "div", "header",
                 "section", "noscript", "ul", "iframe", "body", "nav", "input", "article", "br", "img", "hr", "aside", "content", "table", "tr", "th", "time", "sup", "ol", "tbody", "td"}


class MyBeautifulSoup(BeautifulSoup):
    def _all_strings(self, bs4_element, strip=False, types=(NavigableString, CData)):
        strings = []
        for child in bs4_element.children:
            if isinstance(child, Tag) and child.name == 'a':
                continue
            elif isinstance(child, types):
                strings.extend(self._all_strings(child, strip, types))
            else:
                strings.append(child)
        return strings


def convertToText(soup, fileName):

    if not fileName:
        print('invalid file name')
        return

    with open(fileName, "w", encoding="UTF-8") as f:
        children = list(soup.find_all(setPrint))
        for child in children:
            if child.name == "a":
                href = child.attrs.get("href")
                if href is not None:
                    f.write(child.get_text().strip() + ' ' + href + '\n')
            else:
                f.write(child.get_text().strip() + '\n')

        f.close()


html = "<html><body><h1>Heading</h1><p>Paragraph 1 with foo.</p><p>Paragraph 2 without.</p><a href='https://example.com'>Link</a></body></html>"
soup = MyBeautifulSoup(html, 'html.parser')
print(soup.get_text())

start_url, depth, log_level, secPDFURL, ifSaveHTML = parse_config()
url_info = urlparse(start_url)
# if url_info.path:
#
#    dirPath = 'text/' + url_info.netloc
#    # Get all the text files in the text directory
#    index = 1


#    for file in os.listdir(dirPath):
#
#        file_info = list(os.path.splitext(file))
#        if file_info[1] and file_info[1] == ".html":
#            with open(dirPath + "/" + file) as fp:

# with open(dirPath + "/" + file_info[0] + "-2.txt", "w", encoding="UTF-8") as f:
#
#    f.write(body_text)
#    f.close()

# soup = BeautifulSoup(fp, 'html.parser')
# fp.close()

# children = list(soup.find_all())
# unique_names = set()
# for child in children:
#    unique_names.add(child.name)

# if len(unique_names - setPrint - setContainers) > 0:
#    print('file contains unhandled tags',
#          unique_names - setPrint - setContainers)
#    print(file)
#    print(unique_names, setPrint, setContainers)
# else:
#    convertToText(soup, dirPath + "/" + file_info[0] + ".txt")
