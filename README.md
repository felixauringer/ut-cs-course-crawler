# Crawler for UT course pages

This project is a web crawler that is specifically designed to download all files from the [course page](https://courses.cs.ut.ee) of a course of the Institute of Computer Science at the University of Tartu in Estonia.

## Usage

Start the crawler with `./main.py <start> [--prefix <prefix>]`.

- `<start>` (**required**): The URL where the crawler should start. Because of the navigation on the course website, this can be any URL of the course you want to download (e.g. <https://courses.cs.ut.ee/2022/sa/spring/Main/Labs>).
- `<prefix>` (**optional**): The crawler will only download web pages whose URL starts with this prefix. If this value is not given, the crawler will just use the domain of the start URL (**not recommended**). This should be set to the base URL of the course (e.g. <https://courses.cs.ut.ee/2022/sa/spring>).

The program will create a directory `course-info` in the current working directory and put all the files in there.

## Features

- download linked PDFs (as long as they have the right prefix)
- download the course pages as HTML (without navigation, headers, ...)
- outputs a list of links to external pages (pages not starting with the prefix)

## Problems

- does not download CSS files
- output directory not specifiable

