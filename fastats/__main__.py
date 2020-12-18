#!/usr/bin/env python3

import argparse
import csv
import http.cookiejar
import logging
import pathlib
import re
import sys
from datetime import datetime

import bs4
import requests

from fastats.exceptions import ParsingException

parser = argparse.ArgumentParser()
logger = logging.getLogger()


def get_profile_data(profile: str) -> dict[str, str]:
    page = requests.get('http://www.furaffinity.net/user/{}'.format(profile), cookies=args.cookies)

    if page.status_code != 200:
        raise requests.RequestException('Page status code was not 200 for {}'.format(profile))
    if 'registered users only' in page.text:
        raise requests.RequestException('Profile {} requires authentication and authentication failed'.format(profile))

    soup = bs4.BeautifulSoup(page.text, 'html.parser')
    stats = soup.findAll('div', attrs={'class': 'cell'})

    if not stats:
        raise ParsingException('Could not find any stats')

    # these are all magic numbers at the moment
    flat_stats_1 = list(stats[0].descendants)
    flat_stats_2 = list(stats[1].descendants)

    views = flat_stats_1[3].strip()
    logger.info('{} views'.format(views))

    submissions = flat_stats_1[8].strip()
    logger.info('{} submissions'.format(submissions))

    favourites = flat_stats_1[13].strip()
    logger.info('{} favourites'.format(favourites))

    comments = flat_stats_2[3].strip()
    logger.info('{} comments'.format(comments))

    watchers = soup.find('a', attrs={'target': '_blank'}).text
    watchers = re.search(r'\d+', watchers).group().strip()
    logger.info('{} watchers'.format(watchers))

    return {
        'views': views,
        'submissions': submissions,
        'favourites': favourites,
        'comments': comments,
        'watchers': watchers,
        'user': profile,
        'time': datetime.now().isoformat()}


def _add_parser_options():
    parser.add_argument('--cookies')
    parser.add_argument('-p', '--profile', action='append', default=[])
    parser.add_argument('-f', '--file', help='File to log CSV data to')
    parser.add_argument('--name-file', help='list of profile names to scrape stats from')
    parser.add_argument('-v', '--verbose', action='count', default=0)


def _read_names_from_file(name_file: pathlib.Path) -> list[str]:
    if not name_file.exists():
        raise Exception('Cannot find name file at {}'.format(name_file))
    names = []
    with open(name_file, 'r') as file:
        for line in file.readlines():
            line = line.strip('\n').strip()
            if line:
                names.append(line.strip())
    return names


def _write_data(filename: pathlib.Path, profile_data: list[dict]):
    exists = filename.exists()
    with open(filename, 'a') as file:
        headers = ('time', 'user', 'views', 'submissions', 'favourites', 'comments', 'watchers')
        writer = csv.DictWriter(file, headers)
        if exists is False:
            writer.writeheader()
        for profile in profile_data:
            logger.debug('Writing row of data for profile {}'.format(profile['user']))
            writer.writerow(profile)


def _setup_logger(verbosity_level: int):
    stream = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter('[%(asctime)s - %(levelname)s] - %(message)s')
    stream.setFormatter(formatter)
    logger.addHandler(stream)
    if verbosity_level > 0:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)


if __name__ == "__main__":
    _add_parser_options()
    args = parser.parse_args()

    _setup_logger(args.verbose)

    if args.cookies:
        args.cookies = pathlib.Path(args.cookies).resolve()
        if args.cookies.exists() is False:
            raise Exception('Cookies file not found')
        else:
            args.cookies = http.cookiejar.MozillaCookieJar(args.cookies)
            args.cookies.load()
            logger.debug('Cookies loaded')

    if args.file:
        args.file = pathlib.Path(args.file).resolve()

    if args.name_file:
        args.name_file = pathlib.Path(args.name_file).resolve()
        args.profile.extend(_read_names_from_file(args.name_file))

    collected_data = []
    for profile in args.profile:
        logger.info('Retrieving statistics for profile {}'.format(profile))
        try:
            collected_data.append(get_profile_data(profile))
        except (ParsingException, IndexError, requests.RequestException):
            logger.error('Failed to get statistics for profile {}'.format(profile))

    if args.file:
        _write_data(args.file, collected_data)
        logger.info('Wrote {} profiles to file'.format(len(collected_data)))
