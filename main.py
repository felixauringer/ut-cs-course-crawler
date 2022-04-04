#!/usr/bin/env python3

import argparse
from urllib import parse
import requests
from bs4 import BeautifulSoup
from pathlib import Path


class Crawler:
    def __init__(self, start, prefixes=None):
        start = parse.urlparse(start)._replace(params='', query='', fragment='')
        self.prefixes = []
        if prefixes is None:
            self.prefixes.append(start._replace(path=''))
        else:
            for prefix in prefixes.split(','):
                self.prefixes.append(parse.urlparse(prefix)._replace(params='', query='', fragment=''))
        self.visited = {}
        self.external_links = []
        self.broken_links = []
        self.queue = [start]
        self.link_count = 0
        self.output_directory = Path.cwd().joinpath('course-info')
        Path.mkdir(self.output_directory, exist_ok=True)

    def sanitize(self, url, current):
        url = parse.urlparse(url)._replace(params='', query='', fragment='')
        if not url.netloc:
            # relative url
            url = url._replace(scheme=current.scheme, netloc=current.netloc)
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
        valid_content = True
        try:
            content_type = response.headers['content-type']
        except KeyError:
            content_type = ''
        if 'text/html' in content_type:
            soup = BeautifulSoup(response.text, 'html.parser')
            article = soup.find(name='article', class_='content')
            navigation = soup.find(name='nav', class_='sidebar')
            if article is None:
                if url not in self.broken_links:
                    self.broken_links.append(url)
                valid_content = False
            else:
                body = article.wrap(soup.new_tag('body'))
                html = body.wrap(soup.new_tag('html'))
                content = html.prettify().encode()
                suffix = '.html'

            links = []
            if navigation is not None:
                links += navigation.find_all('a', href=True)
            if article is not None:
                links += article.find_all('a', href=True)
            for link in links:
                self.link_count += 1
                sanitized = self.sanitize(link.get('href'), url)
                if sanitized not in self.visited and any(map(lambda p: sanitized.scheme == p.scheme and
                                                                       sanitized.netloc == p.netloc and
                                                                       sanitized.path.startswith(p.path),
                                                             self.prefixes)):
                    self.queue.append(sanitized)
                elif sanitized not in self.visited and sanitized not in self.external_links:
                    self.external_links.append(sanitized)
        elif 'application/pdf' in content_type:
            content = response.content
            suffix = '.pdf'
        else:
            content = response.content
            suffix = '.bin'
        if valid_content:
            self.visited[url] = (self.url_to_path(url, suffix), content)

    def export_results(self):
        with open(self.output_directory.joinpath('output.txt'), 'w') as out:
            out.write(f'The crawler found {self.link_count} links and downloaded {len(self.visited)} pages.\n')
            if len(self.visited) > 0:
                out.write('The following pages were downloaded and scanned:\n')
            else:
                out.write('No pages were downloaded or scanned.\n')
            for key in sorted(self.visited.keys()):
                out.write(f'\t{key.geturl()}\n')
            if len(self.external_links) > 0:
                out.write('The following external pages were not downloaded or scanned:\n')
            else:
                out.write('No external pages were found.\n')
            for link in sorted(self.external_links):
                out.write(f'\t{link.geturl()}\n')
            if len(self.broken_links) > 0:
                out.write('The following local pages did not contain the expected HTML structure:\n')
            else:
                out.write('No broken local pages were found.\n')
            for link in sorted(self.broken_links):
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
    parser.add_argument('--prefixes', help='only crawl pages matching one of these prefixes (separated with comma)')
    parser.add_argument('start', help='first webpage to crawl')
    args = parser.parse_args()

    crawler = Crawler(args.start, args.prefixes)
    crawler.run()
    crawler.export_results()


if __name__ == '__main__':
    main()
