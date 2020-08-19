#!/usr/bin/env python3

import argparse
import pathlib
import re
import sys
from datetime import datetime
import csv

import bs4
import http.cookiejar
import requests
import logging

parser = argparse.ArgumentParser()


def get_profile_data(page: requests.Response):
    soup = bs4.BeautifulSoup(page.text, 'html.parser')

    stats = soup.findAll('div', attrs={'class': 'cell'})

    views = stats[0].contents[2].strip()
    submissions = stats[0].contents[6].strip()
    favourites = stats[0].contents[10].strip()
    comments = stats[1].contents[2].strip()
    watchers = soup.find('a', attrs={'target': '_blank'}).text
    watchers = re.search(r'\d+', watchers).group()

    logger.info('{} views'.format(views))
    logger.info('{} submissions'.format(submissions))
    logger.info('{} favourites'.format(favourites))
    logger.info('{} comments'.format(comments))
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

    parser.add_argument('cookies')
    parser.add_argument('-p', '--profile', action='append')
    parser.add_argument('-f', '--file')
    parser.add_argument('-v', '--verbose', action='count', default=0)
    args = parser.parse_args()

    if args.verbose > 0:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)

    args.cookies = pathlib.Path(args.cookies).resolve()
    if args.cookies.exists() is False:
        logger.critical('Cannot find cookies file')
        raise Exception('Cookies file not found')
    else:
        args.cookies = http.cookiejar.MozillaCookieJar(args.cookies)

    if args.file:
        args.file = pathlib.Path(args.file).resolve()

    data = []
    for profile in args.profile:
        page = requests.get('http://www.furaffinity.net/user/{}'.format(profile), cookies=args.cookies)
        profile_data = get_profile_data(page)
        data.append((profile, profile_data))

    if args.file:
        exists = args.file.exists()
        with open(args.file, 'a') as file:
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

            for profile in data:
                writer.writerow([
                    datetime.now().isoformat(),
                    profile[0],
                    profile[1]['views'],
                    profile[1]['submissions'],
                    profile[1]['favourites'],
                    profile[1]['comments'],
                    profile[1]['watchers']
                ])
