# gpsadd2exif
A tiny tool for adding GPS info to jpeg image tag (EXIF) using GPX data.

## Prerequisites
```
pip3 install gpxpy gpsphoto ExifRead Pillow
```
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
                        time offset (unit: hour)
```

## Example
```
gpsadd2exif.py --verbose=2 --delta=-9 yamap_2021-06-28_13_30.gpx  FJIMG_20210628_153749.jpg

gpsadd2exif.py --delta=-9 yamap_2021-06-28_13_30.gpx  *

# using system timezone
gpsadd2exif.py yamap_2021-06-28_13_30.gpx  *
```

## Development Environment
* macOS
* Python 3.9.0
