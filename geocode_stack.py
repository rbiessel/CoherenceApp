import os
import glob
import subprocess
from subprocess import Popen, PIPE


# For each interferogram
#   Geocode int (not necessary)
#   Geocode .cor 


latPath = './geom_master/lat.rdr'
lonPath = './geom_master/lon.rdr'
outputTif = True
stackPath = './interferograms/'
boundingBox = '53.38 53.98 -167.25 -166.13'

def execute(cmd):
    print('Running command: ' + cmd)
    rcmd = cmd + ' 2>&1'

    pipe = subprocess.Popen(rcmd, shell=True, stdout=PIPE)
    output = pipe.communicate()[0]
    return_val = pipe.returncode
    print('subprocess return value was ' + str(return_val))
    print(output)
    return output

def geoCodeFile(filePath):
    cmd = f'geocodeGdal.py -l {latPath} -L {lonPath} -f {filePath} -b  \'{boundingBox}\''
    if (outputTif):
        cmd += ' --tiff'
    execute(cmd)  

def main():
    print('Geocoding a stack')
    corPaths = glob.glob('./interferograms/**/filt_fine.cor')

    for x in range(len(corPaths)):
        print(f'Geocoding {corPaths[x]}')
        geoCodeFile(corPaths[x])

if __name__ == '__main__':
    main()

