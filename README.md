# gpsadd2exif
A tiny tool for adding GPS info to jpeg image tag (EXIF) using GPX data.

## Usage
```
usage: gpsadd2exif.py [-h] [-V VERBOSE] [-S] [-D DELTA] gpx_file [jpeg_files ...]

positional arguments:
  gpx_file              a gpx file
  jpeg_files            jpag file(s)

optional arguments:
  -h, --help            show this help message and exit
  -V VERBOSE, --verbose VERBOSE
                        verbose mode: 0, 1 or 2
  -S, --simulation      simulation mode
  -D DELTA, --delta DELTA
                        time offset (unit: hour): hour)
```
