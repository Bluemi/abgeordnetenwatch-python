import html.parser


def get_from_key_list(key_list, key, default=None):
    for k, value in key_list:
        if k == key:
            return value
    return default


class QuestionAnswersParser(html.parser.HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_div = False
        self.hrefs = set()

    def handle_starttag(self, tag, attrs):
        if tag == 'div':
            if 'tile__question__teaser' in get_from_key_list(attrs, 'class', ''):
                self.in_div = True
        elif tag == 'a':
            if self.in_div:
                href = get_from_key_list(attrs, 'href', None)
                if href:
                    if not href.split('/')[-1].isnumeric():
                        self.hrefs.add(href)

    def handle_endtag(self, tag):
        if tag == 'div':
            self.in_div = False
