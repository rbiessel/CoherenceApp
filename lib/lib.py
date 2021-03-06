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
                'size': 8,
                }

    fig, (ax1) = plt.subplots(figsize=(5, 4), ncols=1)
    pos = ax1.imshow(array, cmap='coolwarm', interpolation='none', vmin=vmin, vmax=vmax)

    if title is not None:
        plt.title(title, fontsize=12, fontdict=font)
    if text is not None:
        plt.text(700,500, text, fontsize=10, fontdict=font)
   
    plt.subplots_adjust(left=0.25)
    fig.colorbar(pos, ax=ax1)
    plt.tight_layout()
    
    if filename is not None:
        plt.savefig(filename)
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

def createMeanPngs(stack):
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
        # arrayToTif(corPaths[0], mean, f'output/avg_cor_{baseline}_days.tif')

        data = {
            'title': 'Makushin Volcano and Unalaska Coherence Mean',
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
        dates = interferogram.split('/')
        dates = dates[len(dates) - 2].split('_')
        print(dates)
        date1 = int(dates[0])
        date2 = int(dates[1])
        if date1 not in datelist:
            datelist.append(date1)
        if date2 not in datelist:
            datelist.append(date2)
    return sorted(datelist)

def createMatrix(stack):
    dates = getDates(stack)
    dateTimes = []
    
    for date in dates:
        date = str(date)
        date = datetime.datetime.strptime(date, '%Y%m%d')
        dateTimes.append(date)
    
    dimension = len(dateTimes)

    print(f'Creating a matrix of {dimension}x{dimension}')

    covariance = np.zeros(shape=(dimension, dimension))

    for row in range(dimension):
        for column in range(dimension):
            master = dates[row]
            slave = dates[column]
            if master == slave:
                covariance[row,column] = None
            else:
                covariance[row,column] = getAverageByCombo(master, slave)

    print(covariance)

    data = {
            'title': 'Makushin Coherence Matrix',
            'dates': dates
        }

    displayArray(covariance, data=data, filename='./makushinCovariance.png')


def getAverageByCombo(master, slave):
    path = f'./interferograms/{master}_{slave}/geo_filt_fine.cor'
    print(path)
    return getAverage(path)