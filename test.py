from bs4 import BeautifulSoup, NavigableString, CData, Tag


class MyBeautifulSoup(BeautifulSoup):
    def _all_strings(self, strip=False, types=(NavigableString, CData)):
        for descendant in self.descendants:
            # return "a" string representation if we encounter it
            if isinstance(descendant, Tag) and descendant.name == 'a':
                yield str(descendant)

            # skip an inner text node inside "a"
            if isinstance(descendant, NavigableString) and descendant.parent.name == 'a':
                continue

            # default behavior
            if (
                (types is None and not isinstance(descendant, NavigableString))
                or
                    (types is not None and type(descendant) not in types)):
                continue

            if strip:
                descendant = descendant.strip()
                if len(descendant) == 0:
                    continue
            yield descendant


def parse_html(element):
    output = ''
    if isinstance(element, NavigableString):
        output += element.strip()
    elif element.name == 'a':
        output += element.get_text() + ': ' + element['href'] + ' '
    else:
        for child in element.children:
            output += parse_html(child) + " "

    return output


# Example usage
html = "<html><body><h1>Heading<a href='https://example.com'>Link</a</h1><table><tr><td><a href='https://example.com'>Link</a</td></tr></table><p>Paragraph 1 with foo.</p><p>Paragraph 2 without.</p><a href='https://example.com'>Link</a></body></html>"
soup = MyBeautifulSoup(html, 'lxml')

print(soup.get_text())
