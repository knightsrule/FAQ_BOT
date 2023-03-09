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
    def _all_strings(self, strip=False, types=(NavigableString, CData)):
        # verify types [ADDED]
        if hasattr(types,'__iter__'):
            types = tuple([t for t in types if isinstance(t,type)])
        if types is None: types = NavigableString
        if not types or not isinstance(types, (type, tuple)):
            types = (NavigableString, CData)

        for descendant in self.descendants:
            # return "a" string representation if we encounter it

            if isinstance(descendant, Tag) and descendant.name == 'a':
                yield str('{} {} '.format(descendant.get_text(), descendant.get('href', '')))

            # skip an inner text node inside "a"
            if isinstance(descendant,NavigableString) and descendant.parent.name == 'a':
                continue
            
            if not isinstance(descendant, types): continue # default behavior [EDITED]

            if strip:
                descendant = descendant.strip()
                if len(descendant) == 0:
                    continue
            yield descendant

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


html = "<html><body><h1>Heading<a href='https://example.com'>Link</a></h1><p>Paragraph 1 with foo.</p><p>Paragraph 2 without.</p><a href='https://example.com'>Link</a></body></html>"
#soup = MyBeautifulSoup(html, 'html.parser')
#print(soup.get_text())

start_url, depth, log_level, secPDFURL, ifSaveHTML = parse_config()
url_info = urlparse(start_url)
if url_info.path:

    dirPath = 'text/' + url_info.netloc
    # Get all the text files in the text directory
    index = 1


    for file in os.listdir(dirPath):

        file_info = list(os.path.splitext(file))
        if file_info[1] and file_info[1] == ".html":
            with open(dirPath + "/" + file) as fp:
                soup = MyBeautifulSoup(fp, 'html.parser')
                fp.close()

                with open(dirPath + "/" + file_info[0] + "-2.log", "w", encoding="UTF-8") as f:
                    f.write(soup.get_text())
                    f.close()


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
