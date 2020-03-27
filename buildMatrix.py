import os
import glob
import argparse

from osgeo import gdal
import numpy as np
from matplotlib import pyplot as plt
from osgeo.gdalconst import *
import osr
import datetime
from dateutil.parser import parse
import matplotlib.dates as mdates
from mpl_toolkits.axes_grid1 import make_axes_locatable
from lib import lib as corlib
from matplotlib.ticker import (MultipleLocator, FormatStrFormatter,
                               AutoMinorLocator)


def parse():
    parser = argparse.ArgumentParser(description='Computes a Coherence Matrix given a directory of files')
    
    parser.add_argument('-cdir', '--cor_dir', dest='cor_dir', type=str, required=True,
            help='Coherence input path glob pattern.')

    parser.add_argument('-odir', '--output_file', dest='out_path', type=str, required=True,
            help='Path to write coherence matrix to.')

    return parser

def cmdLineParse():
    parser = parse()
    inps = parser.parse_args()

    inps.cor_dir = os.path.abspath(inps.cor_dir)
    inps.out_path = os.path.abspath(inps.out_path)

    return inps


def displayArray(array, data=None, filename=None):
    vmin = None
    vmax = None
    title = None
    baseline = None
    text = None
    dates = None

    if data:
        if 'dates' in data:
            dates = data['dates']
        if 'title' in data:
            title = data['title']
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

    dates = [date.strftime('%m/%d/%Y') for date in dates]

    fig, (ax1) = plt.subplots(figsize=(6, 6), ncols=1)
    pos = ax1.imshow(array, cmap='coolwarm', interpolation='none', vmin=vmin, vmax=vmax)

    print(dates)
    tickInterval = 4


    x = np.arange(0,len(dates), tickInterval)
    plt.xticks(x, dates[0::tickInterval], rotation=45)
    plt.yticks(x, dates[0::tickInterval], rotation=45)
    ax1.tick_params(axis='both', which='major', labelsize=7)

    ax1.xaxis.set_minor_locator(MultipleLocator(1))
    ax1.yaxis.set_minor_locator(MultipleLocator(1))

    divider = make_axes_locatable(ax1)
    cax = divider.append_axes("right", size="5%", pad=0.05)

    ax1.set_title(title, fontdict=font, pad=16)
    ax1.grid(color='gray', linewidth=0.25)
    plt.subplots_adjust(left=0.25)
    plt.colorbar(pos, cax=cax)
    plt.tight_layout()
    
    if filename is not None:
        plt.savefig(filename, bbox_inches='tight')
        print(f'Wrote matrix to {filename}')
    else:
        plt.show()

def buildPaddedMatrix(stack, out_path):
    dates = corlib.getDates(stack)
    dateTimes = []

    for date in dates:
        date = str(date)
        date = datetime.datetime.strptime(date, '%Y%m%d')
        dateTimes.append(date)

    paddedDates = dateTimes
    x = 0
    while x < len(paddedDates):
        date = paddedDates[x]
        if len(paddedDates) >= x+2:
            x+=1
            date2 = paddedDates[x]
            nextDate = date + datetime.timedelta(days=12)
            if date2.date() != nextDate.date():
                paddedDates.insert(x, nextDate)
        else:
            break
    dimension = len(paddedDates)

    print(f'Creating a matrix of {dimension}x{dimension}')

    covariance = np.zeros(shape=(dimension, dimension))
    for row in range(dimension):
        for column in range(dimension):
            master = paddedDates[row]
            slave = paddedDates[column]
            if master in dateTimes and slave in dateTimes:
                if master == slave:
                    covariance[row,column] = None
                else:
                    master = master.strftime('%Y%m%d')
                    slave = slave.strftime('%Y%m%d')
                    pixelVal = corlib.getAverageByCombo(slave, master)
                    covariance[row,column] = pixelVal
                    if pixelVal is not None: 
                        covariance[row,column] = pixelVal
                        covariance[column,row] = pixelVal

    data = {
        'title': 'Coherence Matrix of Cleveland Volcano and Adjacent Islands',
        'dates': paddedDates
    }

    displayArray(covariance, data=data, filename=out_path)

def getAverageByCombo(master, slave):
    path = f'./interferograms/{master}_{slave}/geo_filt_fine.cor'
    print(path)
    return getAverage(path)

def main():
    corGlobPath = './interferograms/**/geo_filt_fine.cor'
    inps = cmdLineParse()
    stack = glob.glob(inps.cor_dir)
    buildPaddedMatrix(stack, inps.out_path)
    

if __name__ == '__main__':
    main()
    # secondMain()