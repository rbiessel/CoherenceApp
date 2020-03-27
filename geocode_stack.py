import os
import glob
import sys
import subprocess
from subprocess import Popen, PIPE
import argparse


def parse():
    parser = argparse.ArgumentParser(description='Computes a Coherence Matrix given a directory of files')
    
    parser.add_argument('-cdir', '--cor_dir', dest='cor_dir', type=str, required=True,
            help='Coherence input path glob pattern. Must be in quotation marks.')

    parser.add_argument('-odir', '--output_dir', dest='out_dir', type=str, required=True,
            help='Path to geocoded coherence maps to.')
    
    parser.add_argument('-gdir', '--geom_dir', dest='geo_dir', type=str, required=True,
            help='Path to geocoded coherence maps to.')
    
    parser.add_argument('-bbox', '--bounding_box', dest='bbox', type=str, required=True,
            help='Counding box coordinates with quotes.')

    return parser

def cmdLineParse():
    parser = parse()
    inps = parser.parse_args()

    inps.cor_dir = os.path.abspath(inps.cor_dir)
    inps.out_dir = os.path.abspath(inps.out_dir)
    inps.geo_dir = os.path.abspath(inps.geo_dir)

    latPath = os.path.join(inps.geo_dir, 'lat.rdr')
    lonPath = os.path.join(inps.geo_dir, 'lon.rdr')

    if not os.path.exists(latPath):
        print('Could not find geometry LAT.rdr file, exiting...')
        sys.exit()
    
    if not os.path.exists(lonPath):
        print('Could not find geometry LON.rd file, exiting...')
        sys.exit()

    inps.latPath = latPath
    inps.lonPath = lonPath

    return inps


latPath = './geom_master/lat.rdr'
lonPath = './geom_master/lon.rdr'
outputTif = True
stackPath = './interferograms/'
boundingBox = '53.38 53.98 -167.25 -166.13'
boundingBox = '53.835330 53.937098 -166.997493 -166.824826'

def execute(cmd):
    print('Running command: ' + cmd)
    rcmd = cmd + ' 2>&1'

    pipe = subprocess.Popen(rcmd, shell=True, stdout=PIPE)
    output = pipe.communicate()[0]
    return_val = pipe.returncode
    print('subprocess return value was ' + str(return_val))
    print(output)
    return output

def geoCodeFile(filePath, inputs):
    oldPath = os.path.dirname(filePath) + '/geo_filt_fine.cor'
    newPath = inputs.out_dir + '/geo_filt_fine.cor'

    if os.path.exists(oldPath):
        print('Cleaning old file...')
        os.remove(oldPath)

    cmd = f'geocodeGdal.py -l {inputs.latPath} -L {inputs.lonPath} -f {filePath} -b \'{inputs.bbox}\''
    # if (outputTif):
    #     cmd += ' -t'
    execute(cmd)

    # move file to output directory
    print(f'new Path: {newPath}')
    # if not os.path.isdir(inputs.out_dir):
    #     os.makedirs(inputs.out_dir)
    
    # print(oldPath)
    # os.rename(oldPath, newPath)


def main():
    inps = cmdLineParse()

    print('Geocoding a stack')
    corPaths = glob.glob(inps.cor_dir)

    for x in range(len(corPaths)):
        print(f'Geocoding {corPaths[x]}')
        geoCodeFile(corPaths[x], inps)

if __name__ == '__main__':
    main()

