import mistune
import re
import urllib.parse
import hashlib

import es


class CustomRenderer(mistune.Renderer):

    def __init__(self, source, doc_title, url):
        super().__init__()

        self.source = source
        self.doc_title = doc_title
        self.url = url
        self.current_header = []

        self.tables = []
        self.lists = []

        # Insert the document title
        self._insert_content(None, None, [], type='title')

    def header(self, text, level, raw=None):
        self._insert_header(self.remove_tags(text), level)

        rendered_content = super().header(text, level, raw)
        self._insert_content(self.remove_tags(text), rendered_content, self.current_header, type='header')

        return rendered_content

    def paragraph(self, text):
        rendered_content = super().paragraph(text)

        # Insert only if not an image or a link alone
        if not re.compile('^<(img|a).*>$').search(text):
            self._insert_content(text, rendered_content, self.current_header, type='paragraph')

        return rendered_content

    # TODO: we do not index code as hard to deal with it (blocks can be huge so hard to display them in the search)
    # def block_code(self, code, lang=None):
    #     rendered_content = super().block_code(code, lang)
    #     self._insert_content(code, rendered_content, self.current_header, type='code')
    #
    #     return rendered_content

    def table(self, header, body):
        rendered_content = super().table(header, body)

        content = self.remove_tags(header + ' ' + body)
        self._add_entry(content, rendered_content, self.tables, self.current_header, type='table')

        return rendered_content

    def list(self, body, ordered=True):
        rendered_content = super().list(body, ordered)

        self._add_entry(body, rendered_content, self.tables, self.current_header, type='list')

        return rendered_content

    def insert_tables_and_list(self):
        for o in self.tables + self.lists:
            self._insert_content(o['content'], o['rendered_content'], o['headers'], o['type'])

    def _add_entry(self, content, rendered_content, list_content, headers, type):
        duplicates = []

        for o in list_content:
            if o['content'] in content:
                duplicates.append(o)

        # Remove duplicates
        for duplicate in duplicates:
            list_content.remove(duplicate)

        list_content.append({
            'content': content,
            'rendered_content': rendered_content,
            'headers': headers.copy(),
            'type': type,
        })

    def _insert_content(self, content, rendered_content, headers, type):
        doc = {
            'base_link': self.url,
            'link': self.url,  # always use base url in case paragraph under file
        }

        for header in headers:
            level = header['level']
            h = header['h']

            doc['h' + str(level)] = h
            doc['link'] = urllib.parse.urljoin(self.url,
                                               '#' + h.lower().replace(':', '')
                                                              .replace('(', '')
                                                              .replace(')', '')
                                                              .replace('/', '')
                                                              .replace('?', '')
                                                              .replace('!', '')
                                                              .replace('\\', '')
                                                              .replace(',', '')
                                                              .replace(';', '')
                                                              .replace('.', '')
                                                              .replace(' ', '-'))

        if content:
            doc['content'] = content

        if rendered_content:
            doc['rendered_content'] = rendered_content

        doc['title'] = self.doc_title
        doc['source'] = self.source
        doc['type'] = type

        # id = hashlib.md5(doc['rendered_content'].encode("utf-8")).hexdigest()

        es.insert_doc(doc)

    def _insert_header(self, text, level):
        if self.current_header:
            if self.current_header[-1].get('level') == level:
                self.current_header.pop()
                self.current_header.append({
                    'h': text,
                    'level': level
                })

            elif self.current_header[-1].get('level') > level:
                self.current_header.pop()
                self._insert_header(text, level)

            elif self.current_header[-1].get('level') < level:
                self.current_header.append({
                    'h': text,
                    'level': level
                })

        else:
            self.current_header.append({
                'h': text,
                'level': level
            })

    def remove_tags(self, text):
        return re.compile(r'<[^>]+>').sub('', text)

    #
    # NOT NEEDED
    #

    # def image(self, src, title, text):
    #     return ''
    #
    #
    # def inline_html(self, html):
    #     return ''
    #
    # def codespan(seld, text): # inline code
    #     return ''
    #
    # def text(self, text):
    #     return ''
    #
    # def autolink(self, link, is_email=False):
    #     return ''
    #
    # def link(self, link, title, text):
    #     return ''
    #
    # def table_cell(self, content, **flags):
    #     return ''
    #
    # def table_row(self, content):
    #     return ''
    #
    # def list_item(self, text):
    #     return ''


def insert_markdown_doc(source, file_content, title, url):
    renderer = CustomRenderer(source=source, doc_title=title, url=url)
    markdown = mistune.Markdown(renderer=renderer)
    markdown(str(file_content))

    # insert tables and lists
    renderer.insert_tables_and_list()
