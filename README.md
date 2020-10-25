# FA Stats Collector

This is a program that collects the following statistics from a profile page on FurAffinity:

- Views
- Submissions
- Favourites
- Comments
- Watchers

## Options and Arguments

There are the following options and arguments:

- `--cookies`
- `-p, --profile`
- `-f, --file`
- `-v, --verbose`

The `--profile` option can be provided multiple times to fetch the statistics for multiple profiles in a single run.

The `--file` option will write the statistics to the specified file in CSV format, with the current date and time as well.
