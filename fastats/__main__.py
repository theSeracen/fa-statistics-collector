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

parser = argparse.ArgumentParser()


class ParsingException(Exception):
    pass


def get_profile_data(page: requests.Response):
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


if __name__ == "__main__":
    logger = logging.getLogger()
    stream = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter('[%(asctime)s - %(levelname)s] - %(message)s')
    stream.setFormatter(formatter)
    logger.addHandler(stream)

    parser.add_argument('--cookies')
    parser.add_argument('-p', '--profile', action='append')
    parser.add_argument('-f', '--file')
    parser.add_argument('-v', '--verbose', action='count', default=0)
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

    if args.file:
        args.file = pathlib.Path(args.file).resolve()

    data = []
    for profile in args.profile:
        logger.info('Retrieving statistics for profile {}'.format(profile))
        page = requests.get('http://www.furaffinity.net/user/{}'.format(profile), cookies=args.cookies)

        if page.status_code != 200:
            raise Exception('Page status code was not 200 for {}'.format(profile))
        if 'registered users only' in page.text:
            logger.error('Profile {} requires authentication and authentication failed'.format(profile))

        try:
            profile_data = get_profile_data(page)
        except (ParsingException, IndexError):
            profile_data = None

        if profile_data:
            data.append((profile, profile_data))
        else:
            logger.error('Failed to get statistics for profile {}'.format(profile))

    if args.file:
        exists = args.file.exists()
        with open(args.file, 'a') as file:
            writer = csv.writer(file)
            if exists is False:
                logger.debug('Writing CSV header')
                writer.writerow([
                    'Time',
                    'User',
                    'Views',
                    'Submissions',
                    'Favourites',
                    'Comments',
                    'Watchers'
                ])

            for profile in data:
                logger.debug('Writing row of data')
                writer.writerow([
                    datetime.now().isoformat(),
                    profile[0],
                    profile[1]['views'],
                    profile[1]['submissions'],
                    profile[1]['favourites'],
                    profile[1]['comments'],
                    profile[1]['watchers']
                ])
        logger.info('Wrote {} profiles to file'.format(len(data)))
