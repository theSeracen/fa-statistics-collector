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
        'watchers': watchers}


def _add_options():
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
            if line and line != '\n':
                names.append(line.strip())
    return names


def _write_data(filename: pathlib.Path, profile_data: list[tuple[str, dict]]):
    exists = filename.exists()
    with open(filename, 'a') as file:
        writer = csv.writer(file)
        if exists is False:
            writer.writerow([
                'Time',
                'User',
                'Views',
                'Submissions',
                'Favourites',
                'Comments',
                'Watchers'
            ])
        for profile in profile_data:
            logger.debug('Writing row of data for profile {}'.format(profile[0]))
            writer.writerow([
                datetime.now().isoformat(),
                profile[0],
                profile[1]['views'],
                profile[1]['submissions'],
                profile[1]['favourites'],
                profile[1]['comments'],
                profile[1]['watchers']
            ])


if __name__ == "__main__":
    stream = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter('[%(asctime)s - %(levelname)s] - %(message)s')
    stream.setFormatter(formatter)
    logger.addHandler(stream)

    _add_options()
    args = parser.parse_args()

    if args.verbose > 0:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)

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
        args.profile.append(_read_names_from_file(args.name_file))

    collected_data = []
    for profile in args.profile:
        logger.info('Retrieving statistics for profile {}'.format(profile))
        try:
            scraped_data = get_profile_data(profile)
            collected_data.append((profile, scraped_data))
        except (ParsingException, IndexError, requests.RequestException):
            logger.error('Failed to get statistics for profile {}'.format(profile))

    if args.file:
        _write_data(args.file, collected_data)
        logger.info('Wrote {} profiles to file'.format(len(collected_data)))
