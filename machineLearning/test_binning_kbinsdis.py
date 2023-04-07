'''
Wireless Sensor Network
Smart Shower
'''
import os, pathlib, collections, logging
import pandas as pd
import numpy as np
from sklearn.preprocessing import KBinsDiscretizer
from matplotlib import pyplot
from statistics import mean, mode, stdev
import random

# - Discretization using K-means strategy
# - Find bins with highest number of items
# - Check std dev of bin contents
# - Pick bin with most contents and smallest std dev
#   - (using some minimum threshold)

# - Perform this analysis on a separate thread
# - Perform this analysis only when request completed without being cancelled
# - Express time in decimal (maybe percent of a day) for ease of computing std dev, etc.
# - Just send mode of collected temps

"""
    Uncomment code at bottom of scirpt to test script by it self

    To make Random data
    Make sure to import random
    Used to generate random data set.
    The range is the number of days
    time is military time
    Copy output of print to time_data.txt
    print(*[round(random.uniform(0.00, 24.00), 2)
            for x in range(50)], sep='\n')
    print(*[round(random.uniform(7.10, 8.50), 2)
            for x in range(120)], sep='\n')
    print(*[round(random.uniform(8.10, 10.50), 2)
            for x in range(50)], sep='\n')
    print(*[round(random.uniform(17.00, 20.00), 2)
            for x in range(50)], sep='\n')

    how to print the values
    print("deviation %.2f Best time: %.2f" % (stdev(timeBin.binItems), mean(timeBin.binItems)))
"""

# Change this in the future
# User has to have taken a shower for 30 times around the same time
BIN_SIZE_LIMIT = 30
# the time difference in which the user has taken their shower
TIME_STD = 0.50
# Give the user 10 mins before best time
USER_SHOWER_PUSH_FORWARD = 0.17

def doBinning():
    """
        This will return a tuple with (time,temp) ex. (8.35, 74)
        Both, either values can be none ex. (None , None) | ex. (None, 74)
    """

    tempModeValue = mode(cleanList(getDataFromFile(os.path.join(
        str(pathlib.Path(__file__).parent.absolute()), "temperatures.txt"))))
    time = determineUserTime(
        getTimeDataBins(), BIN_SIZE_LIMIT, TIME_STD, USER_SHOWER_PUSH_FORWARD)

    return (time,tempModeValue)

def doBinning_printBins():
    bins = sorted(getTimeDataBins(), key=lambda x: x.binValue, reverse=False)
    print(bins)
    return bins
class BinData:
    def __init__(self, binValue) -> None:
        super().__init__()
        self.binValue = binValue
        self.binItems = []

    def __repr__(self) -> str:
        return "binValue %s | binItems: %s \n" % (self.binValue, self.binItems)
    # Allows print(bins)
    def __str__(self):
        return "binValue %s | binItems: %s \n" % (self.binValue, self.binItems)

def cleanList(unCleanList):
    """
    Takes an 2d array like [[72.0],[73.5]] and converts to
    [72.0, 73.5]
    """
    return [float(item[0]) for item in unCleanList]

def getDataFromFile(fileName):
    """
    fileName = fullFilePath/fileName
    Opens a \\n delimeted file and returns the data as [[value1], [value2]]
    """
    f = None
    list = []
    try:
        f = open(fileName)
        list = [item.split() for item in f.read().split('\n')[:-1]]
    except:
        logging.error("Failed to open file %s" % (fileName))
    finally:
        f.close
    return list

def getTempModeValue():
    timeMode = None

    try:
        timeMode = mode(cleanList(getDataFromFile(os.path.join(
        str(pathlib.Path(__file__).parent.absolute()), "temperatures.txt"))))
    except:
        logging.error("Failed to get mode of time StatisticsError thrown.")

    return timeMode

def getTimeDataBins():
    """
        Gets all the time data and puts them into bins.
    """
    timeData = cleanList(getDataFromFile(os.path.join(str(pathlib.Path(__file__).parent.absolute()),"time_data.txt")))

    myTransformedData = np.array(timeData)
    myTransformedData = myTransformedData.reshape(-1,1)
    # print ("Transformed Data")
    # print(myTransformedData)

    #Creating Kmeans object
    kbinsKmeans = KBinsDiscretizer(n_bins=10, encode='ordinal', strategy='kmeans')
    # Getting and cleaning the so I have a 1 dimensional list
    data_trans_kmeans = cleanList(kbinsKmeans.fit_transform(myTransformedData))
    logging.info("Data Trans = \n" + str(data_trans_kmeans))


    ## Getting the index of the data_trans_kmeans so I can match that to the newDataArray
    ## this way I can map the data_trans_kmeans to the newDataArray
    ## for example 0.0 is [2.0, 3.0, 0.0,...] is index 2 that means in the newData array
    ## [7.56, 7.65, 7.12,...] it's value is 7.21

    # Stores all the bins we have gotten from the data_trans_kmeans
    bins = []

    for index, value in enumerate(data_trans_kmeans):
        if any(bin.binValue == value for bin in bins):
            for bin in bins:
                if bin.binValue == value:
                    bin.binItems.append(timeData[index])
                    break
        else:
            newBin = BinData(value)
            newBin.binItems.append(timeData[index])
            bins.append(newBin)

    # I need to send the list bins to someone
    logging.info("\nSend bins list to someone\n")
    logging.info("Amount of bins " + str(len(bins)) + "\n")
    logging.info([bins])

    return bins


def determineUserTime(bins, BIN_SIZE_LIMIT, TIME_STD, USER_SHOWER_PUSH_FORWARD):
    """
    Takes in bins and determine best user shower time.
    Might return None if no time could be determined.
    """
    #

    filteredBins = [timeBin for timeBin in bins if len(timeBin.binItems) >= BIN_SIZE_LIMIT]
    bestTimeFound = []
    for timeBin in filteredBins:
        #print("deviation %.2f Best time: %.2f" % (stdev(timeBin.binItems), mean(timeBin.binItems)))
        std = stdev(timeBin.binItems)
        if (std <= TIME_STD):
            if len(bestTimeFound) > 0 and bestTimeFound[0] > std:
                bestTimeFound = [std, mean(timeBin.binItems)]
            else:
                bestTimeFound = [std, mean(timeBin.binItems)]

    if (len(bestTimeFound) == 0):
        return 0
    return round(bestTimeFound[1], 2) - USER_SHOWER_PUSH_FORWARD


if __name__ == "__main__":
    # execute only if run as a script
    doBinning_printBins()


# Uncomment Script here to Test binning
#what = doBinning()
#print(what)
