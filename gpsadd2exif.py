#!/usr/bin/env python3
#
# A tiny tool for adding GPS info to jpeg images using GPX data.
#
# Created by Krishna
# krishna@hottuna.tk
#

import os, sys, re, argparse
from PIL import Image
#import PIL.ExifTags as ExifTags
#import xml.etree.ElementTree as ET
from PIL.ExifTags import TAGS, GPSTAGS
import xml.dom.minidom as dom
import gpxpy
import gpxpy.gpx
import time as t
from datetime import datetime, timezone, timedelta
from GPSPhoto import gpsphoto
#import exifread
#from dateutil.parser import parse  #pip3 install python-dateutil

img_datetime_fmt = '%Y:%m:%d %H:%M:%S'
verbose_mode = 1
simulation_mode = False
offset = None  # from OS

def prepare():
    parser = argparse.ArgumentParser(description='Process some integers.')
    parser.add_argument('-V', '--verbose', default=1, type=int, help='verbose mode: 0 or 1')
    parser.add_argument('-S', '--simulation', action='store_true', help='simulation mode')
    parser.add_argument('-D', '--delta',help='time offset (unit: hour)')
    parser.add_argument('gpx_file', help='gpx file')
    parser.add_argument('jpeg_files', nargs='*', help='jpag image(s)')
    opt = parser.parse_args()

    filelist = list()
    for n in opt.jpeg_files:
        match = re.search('\.jpg$|\.jpeg$|\.JPG$|\.JPEG$',n)
        if match:
            filelist.append(n)

    if len(filelist) == 0:
        print('Error: No valid images')
        exit(1)

    # sanity check
    try:
        test = dom.parse(opt.gpx_file)

    except:
        print('Error: gpx parse failed =>', opt.gpx_file)
        exit(1)

    # timezone offset from OS
    system_tz_offset = t.timezone if (t.localtime().tm_isdst == 0) else t.altzone
    system_tz_offset_h = system_tz_offset / 60 / 60 if opt.delta == None else float(opt.delta)
    system_tz_offset = system_tz_offset if opt.delta == None else float(opt.delta) * 60 * 60

    d = open(opt.gpx_file, 'r')
    gpx = gpxpy.parse(d)
    gpx_data = list()
    for track in gpx.tracks:
        for segment in track.segments:
            for point in segment.points:
                gpx_data.append([int(point.time.replace(tzinfo=timezone.utc).timestamp()),
                    round(point.latitude,5), round(point.longitude,5), int(point.elevation)])

    gpx_index = list()
    gpx_index = [n[0] for n in gpx_data]

    return opt, system_tz_offset, gpx_data, gpx_index, filelist


def main(opt, system_tz_offset, gpx_data, gpx_index, fname):
    img = Image.open(fname)
    exif_data = img._getexif()

    if exif_data is not None:
        exif = {
            TAGS[k]: v
            for k, v in img._getexif().items()
            if k in TAGS
        }

        if 'GPSInfo' in exif:
            exifgps = {
                GPSTAGS.get(k, k): exif['GPSInfo'][k]
                for k in exif['GPSInfo'].keys()
            }
        else:
            exifgps = "n/a"

        dt = datetime.strptime(exif['DateTimeOriginal'], img_datetime_fmt)
        utc_time = dt.replace(tzinfo=timezone.utc)
        img_timestamp = int(utc_time.timestamp() + system_tz_offset)
        a = gpx_index.copy()
        a[:] = [x - img_timestamp for x in a]
        b = a.copy()
        b = list(map(abs, b))
        if (max(a) > 0 and min(a) < 0 ):
            p = b.index(min(b))
            v = gpx_index[p]
            try:
                photo = gpsphoto.GPSPhoto(fname)
                utc_time = datetime.utcfromtimestamp(gpx_data[p][0]).strftime('%Y:%m:%d %H:%M:%S')
#                localtime = datetime.utcfromtimestamp(gpx_data[p][0] - system_tz_offset).strftime('%Y:%m:%d %H:%M:%S')
#                info = gpsphoto.GPSInfo((gpx_data[p][1], gpx_data[p][2]), alt=alt, timestamp=localtime)
                info = gpsphoto.GPSInfo((gpx_data[p][1], gpx_data[p][2]), alt=gpx_data[p][3])
                if opt.simulation == False:
                    photo.modGPSData(info, fname)
                print('{0:<32}: success!'.format(fname)) if opt.verbose == 1 else None
                print('{0:<32}: success! => {1} {2}'.format(fname, utc_time, gpx_data[p][1:])) if opt.verbose == 2 else None

            except:
                print('{0:<32}: failed.'.format(fname)) if opt.verbose == 1 or opt.verbose == 2 else None
        elif (max(a) > 0 and min(a) > 0 ) or (max(a) < 0 and min(a) < 0):
            print('{0:<32}: out of range'.format(fname)) if opt.verbose == 1 or opt.verbose == 2 else None
        else:
            print('{0:<32}: unkown error'.format(fname)) if opt.verbose == 1 or opt.verbose == 2 else None


if __name__ == "__main__":
    opt, system_tz_offset, gpx_data, gpx_index, filelist = prepare()
    if opt.simulation == True:
        print('== [Simulation mode] ==')
    for filename in filelist:
        main(opt, system_tz_offset, gpx_data, gpx_index, filename)

