#!/usr/bin/env python3

import argparse
from urllib import parse
import requests
from bs4 import BeautifulSoup
from pathlib import Path


class Crawler:
    def __init__(self, start, prefix=None):
        start = parse.urlparse(start)._replace(params='', query='', fragment='')
        if prefix is None:
            self.prefix = start._replace(path='')
        else:
            self.prefix = parse.urlparse(prefix)._replace(params='', query='', fragment='')
        self.visited = {}
        self.external_links = []
        self.queue = [start]
        self.link_count = 0
        self.output_directory = Path.cwd().joinpath('course-info')
        Path.mkdir(self.output_directory, exist_ok=True)

    def sanitize(self, url, current):
        url = parse.urlparse(url)._replace(params='', query='', fragment='')
        if not url.netloc:
            # relative url
            url = url._replace(scheme=self.prefix.scheme, netloc=self.prefix.netloc)
        if not url.path:
            # was only fragment
            url = url._replace(path=current.path)
        return url

    def url_to_path(self, url, suffix):
        path = Path(parse.unquote(url.path).replace(' ', '_'))
        if path.is_absolute():
            path = Path(*path.parts[1:])
        if not path.suffix:
            path = path.with_suffix(suffix)
        path = self.output_directory.joinpath(path)
        return path

    def run(self):
        while len(self.queue):
            url = self.queue.pop()
            if url in self.visited:
                continue
            self.parse_page(url)

    def parse_page(self, url):
        cookies = dict(userlang='en')
        response = requests.get(url.geturl(), cookies=cookies)
        try:
            content_type = response.headers['content-type']
        except KeyError:
            content_type = ''
        if 'text/html' in content_type:
            soup = BeautifulSoup(response.text, 'html.parser')
            body = soup.find(name='article', class_='content').wrap(soup.new_tag('body'))
            navigation = soup.find(name='nav', class_='sidebar')
            html = body.wrap(soup.new_tag('html'))
            content = html.prettify().encode()
            suffix = '.html'

            for link in body.find_all('a', href=True) + navigation.find_all('a', href=True):
                self.link_count += 1
                sanitized = self.sanitize(link.get('href'), url)
                if sanitized.scheme == self.prefix.scheme and sanitized.netloc == self.prefix.netloc \
                        and sanitized.path.startswith(self.prefix.path) and sanitized not in self.visited:
                    self.queue.append(sanitized)
                elif sanitized not in self.visited and sanitized not in self.external_links:
                    self.external_links.append(sanitized)
        elif 'application/pdf' in content_type:
            content = response.content
            suffix = '.pdf'
        else:
            content = response.content
            suffix = '.bin'
        self.visited[url] = (self.url_to_path(url, suffix), content)

    def export_results(self):
        with open(self.output_directory.joinpath('output.txt'), 'w') as out:
            out.write(f'The crawler found {self.link_count} links and downloaded {len(self.visited)} pages.\n')
            out.write('The following pages were downloaded and scanned:\n')
            for key in self.visited:
                out.write(f'\t{key.geturl()}\n')
            out.write('The following external pages were not downloaded and scanned:\n')
            for link in self.external_links:
                out.write(f'\t{link.geturl()}\n')
        for url, path_content in self.visited.items():
            filename = path_content[0]
            directory = Path(*filename.parts[:-1])
            if not directory.exists():
                directory.mkdir(parents=True)
            with open(filename, 'wb') as out:
                out.write(path_content[1])


def main():
    parser = argparse.ArgumentParser(description='Crawl course pages from courses.cs.ut.ee')
    parser.add_argument('--prefix', help='only crawl pages matching this prefix')
    parser.add_argument('start', help='first webpage to crawl')
    args = parser.parse_args()

    crawler = Crawler(args.start, args.prefix)
    crawler.run()
    crawler.export_results()


if __name__ == '__main__':
    main()

