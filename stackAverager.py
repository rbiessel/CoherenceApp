import os
import glob
from osgeo import gdal
import numpy as np
from matplotlib import pyplot as plt
from osgeo.gdalconst import *
import osr
import datetime
from dateutil.parser import parse
import matplotlib.dates as mdates
import sys

from mpl_toolkits.axes_grid1 import make_axes_locatable


def getAverage(bandName):
    if os.path.exists(bandName):
        raster = gdal.Open(bandName)
        band = raster.GetRasterBand(1)
        return band.ComputeStatistics(0)[2]
    else:
        return None

def rasterAverageStack(stack):
    print('Averaging a stack: ')
    print('Coherence Average: ')
    for x in range(len(stack)):
           print(getAverage(stack[x]))



def bandToArray(rasterPath):
    raster = gdal.Open(rasterPath)
    band = raster.GetRasterBand(1)
    myarray = np.array(band.ReadAsArray())
    # gdal.GDALClose(rasterPath)
    return myarray


def calcSequentialAverage(values, currentAverage, index):
    return (currentAverage * index + values[index]) / (index + 1)


def updateAverage(stack, currentAverage, index):
    nextArray = bandToArray(stack[index])
    newAverage = (currentAverage * index + nextArray) / (index + 1) 
    return newAverage

def buildAverage(stack):
    # Open First Raster
    currentAverage = bandToArray(stack[0])    
    for x in range(len(stack)):
        print(f'Updating average with {stack[x]}')
        currentAverage = updateAverage(stack, currentAverage, x)

    return currentAverage

def displayArray(array, data=None, filename=None):
    vmin = None
    vmax = None
    title = None
    baseline = None
    text = None

    if data:
        if 'title' in data:
            title = data['title']
        if 'baseline' in data:
            baseline = data['baseline']
            baseline = f'Temporal Baseline    =  {baseline} days'

        if 'count' in data:
            count = data['count']
            count =    f'Interferogram Count =  {str(count).zfill(2)}'
            text = f'{baseline}\n{count}'

        if 'min' in data:
            vmin = data['min']
        if 'max' in data:
            vmax = data['max']

        font = {'family': 'serif',
                'fontname': 'arial',
                'color': 'black',
                'weight': 'heavy',
                'size': 12,
                }

    fig, (ax1) = plt.subplots(figsize=(8, 6), ncols=1)
    pos = ax1.imshow(array, cmap='coolwarm', interpolation='none', vmin=vmin, vmax=vmax)

    divider = make_axes_locatable(ax1)
    cax = divider.append_axes("right", size="5%", pad=0.05)

    if title is not None:
        ax1.set_title(title, fontdict=font, pad=16)
    if text is not None:
        ax1.text(25,450, text, fontsize=(font['size'] - 2), fontdict=font)
   
    plt.subplots_adjust(left=0.25)
    fig.colorbar(pos, cax=cax)
    plt.tight_layout()
    
    if filename is not None:
        plt.savefig(filename, bbox_inches='tight')
    else:
        plt.show()


def getBaseline(path):
    dates = path.split('/')[2].split('_')
    date1 = datetime.datetime.strptime(dates[0], '%Y%m%d')
    date2 = datetime.datetime.strptime(dates[1], '%Y%m%d')
    diff = abs(date1 - date2)
    return diff.days

def filterByTempBaseline(stack, tempBase):
    res = [item for item in stack if getBaseline(item) == tempBase]
    return res

def buildBigStack(stack):
    stackAsArrays = []
    for x in range(len(stack)):
        stackAsArrays.append(bandToArray(stack[x]))

    return np.array(stackAsArrays)



def arrayToTif(reference, array, name):
    print('Writing array to GeoTiff....')
    geoRefRaster = gdal.Open(reference)
    driver = geoRefRaster.GetDriver()
    refBand = geoRefRaster.GetRasterBand(1)
    rows = geoRefRaster.RasterYSize
    cols = geoRefRaster.RasterXSize
    print(f'{rows} rows, {cols} columnss')

    output = driver.Create(f'./{name}', cols, rows, 1, GDT_Float32)
    if output is None:
        print(f'Could not create {name}')
        sys.exit(1)

    outBand = output.GetRasterBand(1)
    outBand.WriteArray(array, 0, 0)
    outBand.SetNoDataValue(-99)

    # georeference the image and set the projection
    output.SetGeoTransform(geoRefRaster.GetGeoTransform())
    output.SetProjection(geoRefRaster.GetProjection())
    gdal.Translate(f'{name}', output, format='GTiff')

    # targetProjection = 'WGS84 UTM ZONE 3'
    # target_srs = osr.SpatialReference()
    # target_srs.ImportFromEPSG(4326)
    # target_wkt = target_srs.ExportToWkt()

    # gdal.Warp(f'{name}.tif', output, dstSRS='+proj=utm +zone=3 +datum=WGS84 +units=m +no_defs')
    projection = output.GetProjection()
    print(f'Projection: {projection}')
    output = None
    # outBand.FlushCache()


def getBaselineList(stack):
    baselines = []
    for item in stack:
        baseline = getBaseline(item)
        if baseline not in baselines:
            baselines.append(baseline)
    return baselines

def getMeanByBaseline(baseline, stack):
    if (isinstance(baseline, int)):
        print(f'Using baseline: {baseline} days')
        stack = filterByTempBaseline(stack, baseline)
        # print(stack)
    if (baseline == 'all'):
        print(stack)

    print(f'Calculating coherence mean from {len(stack)} interferograms with baseline of {baseline} days')
    npStack = buildBigStack(stack)
    return np.mean(npStack, axis=0), len(stack)

def createMeanPngs(corPaths):
    print('Baseline: ')
    print(getBaseline(corPaths[0]))
    baselines = getBaselineList(corPaths)
    # baselines = [12]
    baselines.sort()

    for baseline in baselines:
        mean, count = getMeanByBaseline(baseline, corPaths)

        meanMin = np.amin(mean)
        meanMax = np.amax(mean)

        print(f'Min: {meanMin} Max: {meanMax}')
        # # std = np.std(npStack, axis=0)
        baseline = str(baseline).zfill(3)
        arrayToTif(corPaths[0], mean, f'./meanByTempBaseline/avg_cor_{baseline}_days.tif')

        data = {
            'title': 'Northwestern Unalaska Coherence Mean',
            'baseline': baseline,
            'count': count,
            'min': 0,
            'max': 1
        }
        fileName = f'./meanByTempBaseline/meanCor-{baseline}days.png'
        displayArray(mean, data=data, filename=fileName)


def getDates(stack):
    datelist = []
    for interferogram in stack:
        dates = interferogram.split('/')[2].split('_')
        date1 = int(dates[0])
        date2 = int(dates[1])
        if date1 not in datelist:
            datelist.append(date1)
        if date2 not in datelist:
            datelist.append(date2)
    return sorted(datelist)


def main():
    outname = './geocoded_average.cor'
    corGlobPath = './interferograms/**/geo_filt_fine.cor'
    stack = glob.glob(corGlobPath)
    createMeanPngs(stack)
    # averagedStack = buildAverage(corPaths)
    # displayArray(averagedStack)
    # Get geo info from stack raster

    
if __name__ == '__main__':
    main()
    # secondMain()