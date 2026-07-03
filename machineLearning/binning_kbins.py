"""
Habit-recognition helpers for Smart Shower.

The module reads newline-delimited shower temperatures and shower start times,
groups the time data into K-means bins, and returns the strongest time and
temperature suggestion for the mobile app notification flow.
"""

import logging
import pathlib
from statistics import mean, mode, stdev

import numpy as np
from sklearn.preprocessing import KBinsDiscretizer

BIN_SIZE_LIMIT = 30
TIME_STD = 0.50
USER_SHOWER_PUSH_FORWARD = 0.17

DATA_DIR = pathlib.Path(__file__).parent.absolute()
TEMPERATURES_FILE = DATA_DIR / "temperatures.txt"
TIME_DATA_FILE = DATA_DIR / "time_data.txt"


class BinData:
    def __init__(self, binValue) -> None:
        self.binValue = binValue
        self.binItems = []

    def __repr__(self) -> str:
        return "binValue %s | binItems: %s \n" % (self.binValue, self.binItems)

    def __str__(self):
        return "binValue %s | binItems: %s \n" % (self.binValue, self.binItems)


def cleanList(unCleanList):
    """
    Convert a two-dimensional list like [["72.0"], ["73.5"]] into floats.
    """
    return [float(item[0]) for item in unCleanList if len(item) > 0]


def getDataFromFile(fileName):
    """
    Read a newline-delimited data file and return values as ``[[value], ...]``.
    """
    try:
        with open(fileName, encoding="utf-8") as data_file:
            return [item.split() for item in data_file.read().splitlines() if item.strip()]
    except OSError:
        logging.error("Failed to open file %s", fileName)
        return []


def getTempModeValue():
    tempMode = None

    try:
        tempMode = mode(cleanList(getDataFromFile(TEMPERATURES_FILE)))
    except Exception:
        logging.error("Failed to get mode of temperature data.")

    return tempMode


def getTimeDataBins(fileName=TIME_DATA_FILE, number_of_bins=10):
    """
    Read shower time data and group it into K-means bins.
    """
    timeData = cleanList(getDataFromFile(fileName))
    if not timeData:
        return []

    number_of_bins = min(number_of_bins, len(timeData))
    transformed = np.array(timeData).reshape(-1, 1)

    kbinsKmeans = KBinsDiscretizer(
        n_bins=number_of_bins,
        encode="ordinal",
        strategy="kmeans",
        subsample=None,
    )
    data_trans_kmeans = cleanList(kbinsKmeans.fit_transform(transformed))
    logging.info("Data Trans = \n%s", data_trans_kmeans)

    bins = []
    for index, value in enumerate(data_trans_kmeans):
        existing_bin = next((time_bin for time_bin in bins if time_bin.binValue == value), None)
        if existing_bin:
            existing_bin.binItems.append(timeData[index])
        else:
            newBin = BinData(value)
            newBin.binItems.append(timeData[index])
            bins.append(newBin)

    logging.info("Amount of bins %s", len(bins))
    logging.info("%s", bins)

    return bins


def determineUserTime(bins, BIN_SIZE_LIMIT, TIME_STD, USER_SHOWER_PUSH_FORWARD):
    """
    Return the suggested shower time, or 0 when no stable shower-time bin exists.
    """
    filteredBins = [timeBin for timeBin in bins if len(timeBin.binItems) >= BIN_SIZE_LIMIT]
    bestTimeFound = None

    for timeBin in filteredBins:
        std = stdev(timeBin.binItems)
        if std <= TIME_STD:
            candidate = (std, -len(timeBin.binItems), mean(timeBin.binItems))
            if bestTimeFound is None or candidate < bestTimeFound:
                bestTimeFound = candidate

    if bestTimeFound is None:
        return 0

    return round(bestTimeFound[2], 2) - USER_SHOWER_PUSH_FORWARD


def doBinning():
    """
    Return a ``(time, temperature)`` tuple such as ``(8.35, 74.0)``.
    """
    tempModeValue = mode(cleanList(getDataFromFile(TEMPERATURES_FILE)))
    time = determineUserTime(
        getTimeDataBins(), BIN_SIZE_LIMIT, TIME_STD, USER_SHOWER_PUSH_FORWARD
    )

    return (time, tempModeValue)


def doBinning_printBins():
    bins = sorted(getTimeDataBins(), key=lambda x: x.binValue, reverse=False)
    print(bins)
    return bins


if __name__ == "__main__":  # pragma: no cover
    doBinning_printBins()
