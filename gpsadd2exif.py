#!/usr/bin/env python3
#
# A tiny tool for adding GPS info to jpeg images using GPX data.
#
# Created by Krishna
# krishna@hottunalabs.net
#

import os, sys, re, argparse
import time as t
from pathlib import Path
from PIL import Image
#import PIL.ExifTags as ExifTags
#import xml.etree.ElementTree as ET
from PIL.ExifTags import TAGS, GPSTAGS
import xml.dom.minidom as dom
import gpxpy
import gpxpy.gpx
from datetime import datetime, timezone, timedelta
from GPSPhoto import gpsphoto
#from geojson import Feature, MultiLineString, FeatureCollection
import geojson

#import exifread
#from dateutil.parser import parse  #pip3 install python-dateutil

img_datetime_fmt = '%Y:%m:%d %H:%M:%S'
verbose_mode = 1
simulation_mode = False
offset = None  # from OS

def prepare():
    parser = argparse.ArgumentParser(description='')
    parser.add_argument('-V', '--verbose', default=1, type=int, help='verbose mode: 0, 1 or 2')
    parser.add_argument('-S', '--simulation', action='store_true', help='simulation mode')
    parser.add_argument('-I', '--info', action='store_true', help='gpx info')
    parser.add_argument('-D', '--delta', help='time offset (unit: hour)')
    parser.add_argument('-T', '--template', type=str, help='generate leaflet shortcode')
    parser.add_argument('-G', '--geojson', action='store_true', help='convert from GPX to Giojson')
    parser.add_argument('gpx_file', help='a gpx file')
    parser.add_argument('jpeg_files', nargs='*', help='jpag file(s)')
    opt = parser.parse_args()

    filelist = list()
    for n in opt.jpeg_files:
        #match = re.search('.jpg$|.jpeg$|.JPG$|.JPEG$|.avif$',n)
        match = re.search('.jpg$|.jpeg$|.JPG$|.JPEG$',n)
        if match:
            filelist.append(n)

    if opt.info == False and opt.geojson == False:
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
    gpx_name = gpx.tracks[0].name
    for track in gpx.tracks:
        for segment in track.segments:
            for point in segment.points:
                p_time = int(point.time.replace(tzinfo=timezone.utc).timestamp()) if not point.time is None else -1
                p_ele = int(point.elevation) if not point.elevation is None else -1
                gpx_data.append([p_time,
                    round(point.latitude,7), round(point.longitude,7), p_ele])

    gpx_index = list()
    gpx_index = [n[0] for n in gpx_data]

    return opt, system_tz_offset, gpx_data, gpx_index, gpx_name, filelist

def info(gpx_data):
    ti = [x[0] for x in gpx_data]
    lat = [x[1] for x in gpx_data]
    lon = [x[2] for x in gpx_data]
    ele = [x[3] for x in gpx_data]
    print("\n == [GPX info] ==\n")
    print(f' Min Coordinate          : [ {min(lat)}, {min(lon)} ]')
    print(f' Max Coordinate          : [ {max(lat)}, {max(lon)} ]')
    latCenter = (min(lat) + max(lat)) * 0.5
    lonCenter = (min(lon) + max(lon)) * 0.5
    print(f' Center Coordinate       : [ {latCenter}, {lonCenter} ]')
    print(f' Start Coordinate        : [ {lat[0]}, {lon[0]} ]')
    print(f' End Coordinate          : [ {lat[-1]}, {lon[-1]} ]')
    print(f' Start and End time      : [ {min(ti)}, {max(ti)} ]')
    print(f' Min and Max elevation   : [ {min(ele)}, {max(ele)} ]')

def conv_geojson(gpx_data, gpx_name, gpx_file):
    x = lambda a: [a[2], a[1], a[3]]
    gpx_data = [ x(n) for n in gpx_data ]
    geo_mline = geojson.MultiLineString([tuple(gpx_data)])
    geo_feature = geojson.Feature(geometry=geo_mline)
    geo_feature["properties"]["name"] = gpx_name
    geo_data = geojson.FeatureCollection([geo_feature])
    
    fname = Path(gpx_file)
    fname = str(fname.with_suffix('')) + '.geojson'
    dump = geojson.dumps(geo_data, sort_keys=True)
    with open(fname, "w") as f:
        f.write(dump)
    
    

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
                #utc_time = datetime.utcfromtimestamp(gpx_data[p][0]).strftime('%Y:%m:%d %H:%M:%S')
                utc_time = datetime.fromtimestamp(gpx_data[p][0], timezone.utc).strftime('%Y:%m:%d %H:%M:%S')
#                localtime = datetime.utcfromtimestamp(gpx_data[p][0] - system_tz_offset).strftime('%Y:%m:%d %H:%M:%S')
#                info = gpsphoto.GPSInfo((gpx_data[p][1], gpx_data[p][2]), alt=alt, timestamp=localtime)
                info = gpsphoto.GPSInfo((gpx_data[p][1], gpx_data[p][2]), alt=gpx_data[p][3])
                if opt.simulation == True:
                    #print('{0:<32}: success!'.format(fname)) if opt.verbose == 1 else None
                    print(f'{fname:<32} <DATE> {utc_time}, <LOCATION> {gpx_data[p][1:]}')
                elif opt.template != None:
                        temp = opt.template
                        lat, lng, ele = gpx_data[p][1:]
                        with open(temp, 'r') as f:
                            s = f.read()
                            print(eval(s))
                else:
                    photo.modGPSData(info, fname)
                    print(f'{fname:<32}: success!') if opt.verbose == 1 else None
                    print(f'{fname:<32}: success! => {utc_time} {gpx_data[p][1:]}') if opt.verbose == 2 else None

            except:
                print(f'{fname:<32}: failed.'.format()) if opt.verbose == 1 or opt.verbose == 2 else None
        elif (max(a) > 0 and min(a) > 0 ) or (max(a) < 0 and min(a) < 0):
            print(f'{fname:<32}: out of range') if opt.verbose == 1 or opt.verbose == 2 else None
        else:
            print(f'{fname:<32}: unkown error') if opt.verbose == 1 or opt.verbose == 2 else None


if __name__ == "__main__":
    opt, system_tz_offset, gpx_data, gpx_index, gpx_name, filelist = prepare()
    if opt.simulation == True:
        print("\n == [Simulation mode] ==\n")
    elif opt.info == True:
        info(gpx_data)
    elif opt.geojson == True:
        conv_geojson(gpx_data, gpx_name, opt.gpx_file)
        
    for filename in filelist:
        main(opt, system_tz_offset, gpx_data, gpx_index, filename)

