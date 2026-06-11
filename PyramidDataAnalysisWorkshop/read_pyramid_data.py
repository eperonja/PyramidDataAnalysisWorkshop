import re
import sys
import math
from mplcursors import cursor
from dateutil import parser
from alive_progress import alive_bar
from collections import Counter
from itertools import groupby
from typing import Any, Dict, Tuple, List
from pathlib import Path
import os

# global data variables
xCoord = []
yCoord = []
subtractPedX = []
subtractPedY = []
eventTime = []
tracking6MiddleMissedXY = []
tracking6MiddleMissedX = []
tracking6MiddleMissedY = []
tracking6MiddleHitsXsingleBothLayers = []
tracking6MiddleHitsXsingleTopBottom = []
tracking6MiddleHitsYsingleTopBottom = []
tracking6MiddleHitsXY = []
tracking6MiddleHitsOnlyX = []
tracking6MiddleHitsOnlyY = []
tracking5TopMissingX = []
tracking5MiddleMissingX = []
tracking5BottomMissingX = []
tracking5TopMissingY = []
tracking5MiddleMissingY = []
tracking5BottomMissingY = []
tracking4TopMissing = []
tracking4MiddleMissing = []
tracking4BottomMissing = []

# open and load config files
geometry_config_file = resource_path("config/geometry_header.txt")
# config variables
geometry = []
singleGeometry = []
geometryHeader = []
with open(geometry_config_file) as gcf:
    lines = gcf.read().splitlines()
    with alive_bar(len(lines)) as bar:
        for i in range(len(lines)):
            if lines[i].startswith('ATH'):
                if len(singleGeometry) > 0:
                    geometry.append(singleGeometry)
                    singleGeometry = []
                singleGeometry.append(lines[i].split(" "))
            if lines[i].startswith('P') and not lines[i].startswith('Plane'):
                singleGeometry.append(lines[i].split(" "))
            bar.title('Loading Geometry...')
            bar()
        geometry.append(singleGeometry)

pedestal_config_file = resource_path("config/pedestal.txt")
pedestal = []
name = []
singlePedestal = []
with open(pedestal_config_file) as pcf:
    lines = pcf.read().splitlines()
    with alive_bar(len(lines)) as bar:
        for i in range(len(lines)):
            if lines[i].startswith('ATH'):
                mapname = []
                mapname.append(lines[i])
            if lines[i].startswith('Mod'):
                if len(singlePedestal) > 0:
                    pedestal.append(singlePedestal)
                singlePedestal = []
                singlePedestal.append([mapname, lines[i].strip()])
            if len(lines[i]) > 0 and lines[i][0].isdigit():
                singlePedestal.append(lines[i].split(" "))
            bar.title('Loading Pedestal...')
            bar()
    pedestal.append(singlePedestal)

adcmap_config_file = resource_path("config/adcmap.txt")
adcmap = []
mapname = []
moddata = []
singleADCmap = []
with open(adcmap_config_file) as acf:
    lines = acf.read().splitlines()
    with alive_bar(len(lines)) as bar:
        for i in range(len(lines)):
            if lines[i].startswith('ATH'):
                mapname = []
                mapname.append(lines[i])
            if lines[i].startswith('Mod'):
                if len(singleADCmap) > 0:
                    adcmap.append(singleADCmap)
                singleADCmap = []
                singleADCmap.append([mapname, lines[i].strip(), lines[i + 1].strip()])
            if len(lines[i]) > 0 and lines[i][0].isdigit():
                singleADCmap.append(lines[i].split(" "))
            bar.title('Loading ADCmap...')
            bar()
    adcmap.append(singleADCmap)

# data variables
input_lines = []
header_time = ''
header_date = ''
header_lines = []
comments = ''
detector = []
df = []
if 'runComments' not in globals() or not globals().get('runComments'):
    runComments = "- Run comments"

with open(input_file_name) as ifn:
    lines = ifn.read().splitlines()
    with alive_bar(len(lines)) as bar:
        for i in range(len(lines)):
            if lines[i].startswith('/') or lines[i].strip().startswith('Tstamp_us'):
                header_lines.append(lines[i])
                if lines[i].startswith("// Run start time:"):
                    date_time = lines[i].split()
                    header_date = "".join([date_time[6], date_time[5].upper(), date_time[8]])
                    header_time = date_time[7]
            else:
                if lines[i].startswith("COMMENTS"):
                    # Preserve any channel-range info that was set earlier from the
                    # command-line arguments. If runComments already contains the
                    # "Using channel ranges" string, append the COMMENTS line so
                    # both appear in chart titles. Otherwise just use the COMMENTS.
                    if runComments and runComments != "- Run comments":
                        runComments = f"{runComments} {lines[i]}"
                    else:
                        runComments = lines[i]
                else:
                    if lines[i].startswith("ATH"):
                        detector = lines[i]
                        detector = detector.strip().split(" ")
                    # print(i, detector)
                    else:
                        df.append(lines[i].strip().split("\t"))
            bar.title('Loading Data File...')
            bar()
        df.append(lines[len(lines) - 1].strip().split("\t"))


def getGeometryLayers(g):
    layers = []
    with alive_bar(len(g)) as bar:
        for i in range(len(g)):
            singleLayer = []
            if g[i][0].startswith('P'):
                for j in range(3, len(g[i]) - 2):
                    singleLayer.append(g[i][j])
                layers.append(singleLayer)
            bar.title('Getting geometry layers...')
            bar()
    return layers
#end of getGeometryLayers

# functions
def retrieveTimedData(option, d, arr):
    timedData = []
    done = False
    with alive_bar(len(arr)) as bar:
        for i in range(len(arr)):
            dataDetector = d[0]
            dataDate = d[2]
            dataTime = d[3]
            if option == 'geometry':
                arrDetector = arr[i][0][0]
                arrDate = arr[i][0][1]
                arrTime = arr[i][0][2]
                # print(option, arrDetector, arrDate, arrTime)
                if dataDetector == arrDetector:
                    dDate = parser.parse(' '.join([dataDate, dataTime]))
                    aDate = parser.parse(' '.join([arrDate, arrTime]))
                    if dDate > aDate and not done:
                        timedData = arr[i]
                        done = True
            if option == 'pedestal':
                pedestalData = arr[i][0][0][0].split(" ")
                arrDetector = pedestalData[0]
                arrDate = pedestalData[1]
                arrTime = pedestalData[2]
                # print(option, arrDetector, arrDate, arrTime)
                if dataDetector == arrDetector:
                    dDate = parser.parse(' '.join([dataDate, dataTime]))
                    aDate = parser.parse(' '.join([arrDate, arrTime]))
                    if dDate > aDate and not done:
                        completedMod = arr[i][1] + arr[i][2] + arr[i][3] + arr[i][4]
                        completedMod = [x for x in completedMod if x]
                        timedData.append(completedMod)
                        if arr[i][0][1] == 'Mod5':
                            done = True
            if option == 'adcmap':
                pedestalData = arr[i][0][0][0].split(" ")
                arrDetector = pedestalData[0]
                arrDate = pedestalData[1]
                arrTime = pedestalData[2]
                # print(option, arrDetector, arrDate, arrTime)
                if dataDetector == arrDetector:
                    dDate = parser.parse(' '.join([dataDate, dataTime]))
                    aDate = parser.parse(' '.join([arrDate, arrTime]))
                    if dDate > aDate and not done:
                        completedMod = arr[i][1] + arr[i][2] + arr[i][3] + arr[i][4]
                        completedMod = [x for x in completedMod if x]
                        timedData.append(completedMod)
                        if arr[i][0][1] == 'Mod5':
                            done = True
            bar.title('Getting timed ' + option + ' ...')
            bar()
    return timedData
#end of retrieveTimedData

def getADCPosition(mod, channel, adcmap):
    mapPosition = 0
    for i in range(len(adcmap[mod])):
        if int(adcmap[mod][i]) > 0 and (channel + 1) == int(adcmap[mod][i]):
            mapPosition = i + 1
    return mapPosition
#end of getADCPosition

def getPedestalValue(mod, channel, pedestal):
    pedestalValue = 0
    for i in range(len(pedestal[mod])):
        if i == channel:
            pedestalValue = int(pedestal[mod][i])
    return pedestalValue
#end of getPedestalValue

# Build fast lookup maps once (call after you load `adcmap` and `pedestal`)
def build_adc_lookup(adcmap: List[List[List[str]]]) -> Dict[Tuple[int, int], int]:
    """
    Build a dict mapping (mod, channel) -> mapPosition (int).
    Assumes numeric entries in inner lists; mirrors original logic.
    """
    lookup: Dict[Tuple[int, int], int] = {}
    for mod_index, mod_entries in enumerate(adcmap):
        # flattened numeric tokens within this mod, tolerant to nested lists/strings
        for i, token in enumerate(mod_entries):
            val = None
            # token may be a string/int or a nested list/tuple
            if isinstance(token, (str, int)):
                try:
                    val = int(token)
                except Exception:
                    continue
            elif isinstance(token, (list, tuple)) and token:
                try:
                    val = int(token[0])
                except Exception:
                    continue
            else:
                continue
            if val is not None and val > 0:
                # original compared (channel+1) == int(adcmap[mod][i])
                # so map the channel (val-1) to position i+1
                channel = val - 1
                lookup[(mod_index, channel)] = i + 1
    return lookup
#end of build_adc_lookup

def build_pedestal_lookup(pedestal: List[List[str]]) -> Dict[Tuple[int, int], int]:
    """
    Build a dict mapping (mod, channel) -> pedestalValue (int).
    Assumes pedestal[mod][channel] is numeric or convertible.
    """
    lookup: Dict[Tuple[int, int], int] = {}
    for mod_index, mod_entries in enumerate(pedestal):
        for ch_index, token in enumerate(mod_entries):
            try:
                val = int(token)
            except Exception:
                # tolerate nested/wrapped formats
                if isinstance(token, (list, tuple)) and token:
                    try:
                        val = int(token[0])
                    except Exception:
                        continue
                else:
                    continue
            lookup[(mod_index, ch_index)] = val
    return lookup
#end of build_pedestal_lookup

# Faster event grouping: df is list of rows where df[i][1] == event id
def group_events_by_id(df: List[List[str]]):
    # Ensure df sorted by event id (int at index 1)
    df_sorted = sorted(df, key=lambda r: int(r[1]))
    for event_id, rows in groupby(df_sorted, key=lambda r: int(r[1])):
        yield event_id, list(rows)
#end of group_events_by_id

# Optimized replacement for getEventDetails
def get_event_details(event_id: int, df: List[List[str]], layerMaxSize: int, minPed: int,
                      pedestal_lookup: Dict[Tuple[int, int], int], adc_lookup: Dict[Tuple[int, int], int]):
    global eventTime
    global xCoord
    global yCoord
    global subtractPedX
    global subtractPedY
    tempTime = [0.0] * 6

    tempX = [[[0 for _ in range(4)] for _ in range(layerMaxSize)] for _ in range(3)]
    tempY = [[[0 for _ in range(4)] for _ in range(layerMaxSize)] for _ in range(3)]
    tempSubtractPedX = [[0 for _ in range(layerMaxSize)] for _ in range(3)]
    tempSubtractPedY = [[0 for _ in range(layerMaxSize)] for _ in range(3)]
    for row in df:
        et = float(row[0])
        brd = int(row[2])
        ch = int(row[3])
        lg = int(row[4])
        layer_index = brd // 2  # 0..2 for the three X (even) / Y (odd) pairs
        is_x = (brd % 2 == 0)
        if is_x:
            # modules corresponding to X: 0,2,4 in original
            mod = layer_index * 2  # maps 0->0,1->2,2->4
            ped = pedestal_lookup.get((mod, ch), 0)
            map_pos = adc_lookup.get((mod, ch), 0)
            new_lg = lg - ped
            if new_lg < minPed:
                new_lg = 0
                count_hit = False
            else:
                count_hit = True
            entry = tempX[layer_index][ch]
            entry[0] = map_pos
            entry[1] = lg
            entry[2] = ped
            entry[3] = new_lg
            entry = tempY[layer_index][ch]
            entry[0] = map_pos
            entry[1] = lg
            entry[2] = ped
            entry[3] = new_lg
            # if lg > 0:
            #	print(entry)
            tempSubtractPedY[layer_index][ch] = new_lg
            if count_hit:
                tempTime[int(brd)] = et  # type: ignore
    eventTime.append(tempTime)
    xCoord.append(tempX)
    yCoord.append(tempY)
    subtractPedX.append(tempSubtractPedX)
    subtractPedY.append(tempSubtractPedY)
#end of get_event_details

def getEventDetails(id, dfportion, layerMaxSize, minPed, pedestal, adcmap):
    global eventTime
    global xCoord
    global yCoord
    global subtractPedX
    global subtractPedY
    tempTime: List[float] = [0.0 for i in range(6)]
    tempX = [[[0 for x in range(4)] for i in range(layerMaxSize)] for j in range(3)]
    tempY = [[[0 for x in range(4)] for i in range(layerMaxSize)] for j in range(3)]
    tempSubtractPedX = [[0 for i in range(layerMaxSize)] for j in range(3)]
    tempSubtractPedY = [[0 for i in range(layerMaxSize)] for j in range(3)]
    countPerEvent = 0
    countX = 0
    countY = 0
    for ndx in range(0, layerMaxSize):
        tempX[0][ndx][0] = getADCPosition(0, ndx, adcmap)
        tempX[0][ndx][2] = getPedestalValue(0, ndx, pedestal)
        tempX[1][ndx][0] = getADCPosition(2, ndx, adcmap)
        tempX[1][ndx][2] = getPedestalValue(2, ndx, pedestal)
        tempX[2][ndx][0] = getADCPosition(4, ndx, adcmap)
        tempX[2][ndx][2] = getPedestalValue(4, ndx, pedestal)
        tempY[0][ndx][0] = getADCPosition(1, ndx, adcmap)
        tempY[0][ndx][2] = getPedestalValue(1, ndx, pedestal)
        tempY[1][ndx][0] = getADCPosition(3, ndx, adcmap)
        tempY[1][ndx][2] = getPedestalValue(3, ndx, pedestal)
        tempY[2][ndx][0] = getADCPosition(5, ndx, adcmap)
        tempY[2][ndx][2] = getPedestalValue(5, ndx, pedestal)
    for i in range(len(dfportion)):
        countHit = True
        brd = int(dfportion[i][2])
        ch = int(dfportion[i][3])
        lg = int(dfportion[i][4])
        # check if it X or Y layer
        if brd % 2 == 0:
            newLg = lg - tempX[brd // 2][ch][2]
            if newLg < minPed:
                newLg = 0
                countHit = False
            tempX[brd // 2][ch][1] = lg
            tempX[brd // 2][ch][3] = newLg
            tempSubtractPedX[brd // 2][ch] = newLg
            countX += 1
            et = float(dfportion[i][0])
            if countHit:
                tempTime[int(brd)] = et
        else:
            newLg = lg - tempY[brd // 2][ch][2]
            if newLg < minPed:
                newLg = 0
                countHit = False
            tempY[brd // 2][ch][1] = lg
            tempY[brd // 2][ch][3] = newLg
            tempSubtractPedY[brd // 2][ch] = newLg
            countY += 1
            et = float(dfportion[i][0])
            if countHit:
                tempTime[int(brd)] = et
        countPerEvent += 1
    eventTime.append(tempTime)
    xCoord.append(tempX)
    yCoord.append(tempY)
    subtractPedX.append(tempSubtractPedX)
    subtractPedY.append(tempSubtractPedY)
#end of getEventDetails

# need to match the datafile to the configuration files
dataGeometry = retrieveTimedData('geometry', detector, geometry)
layers = getGeometryLayers(dataGeometry)
dataPedestal = retrieveTimedData('pedestal', detector, pedestal)
dataADCmap = retrieveTimedData('adcmap', detector, adcmap)

# get layerOrder
layerOrderX = []
layerOrderY = []
layerOrderX.append([float(dataGeometry[1][len(dataGeometry[1]) - 4]), 5, 0])
layerOrderX.append([float(dataGeometry[3][len(dataGeometry[3]) - 4]), 3, 1])
layerOrderX.append([float(dataGeometry[5][len(dataGeometry[5]) - 4]), 1, 2])
layerOrderX = sorted(layerOrderX, key=lambda x: x[0])
layerOrderY.append([float(dataGeometry[2][len(dataGeometry[2]) - 4]), 6, 0])
layerOrderY.append([float(dataGeometry[4][len(dataGeometry[4]) - 4]), 4, 1])
layerOrderY.append([float(dataGeometry[6][len(dataGeometry[6]) - 4]), 2, 2])
layerOrderY = sorted(layerOrderY, key=lambda x: x[0])

layerMaxSize = 64
detectorName = detector[0]
minPed = int(detector[len(detector) - 1])
currentEvent = 0
pointTolerance = 3.0
eventDf = []

with alive_bar(len(df)) as bar:
    for i in range(len(df)):
        if currentEvent == int(df[i][1]):
            eventDf.append(df[i])
        else:
            getEventDetails(currentEvent, eventDf, layerMaxSize, minPed, dataPedestal, dataADCmap)
            eventDf = []
            currentEvent = int(df[i][1])
            eventDf.append(df[i])
        bar.title('Loading all events in memory...')
        bar()
getEventDetails(currentEvent, eventDf, layerMaxSize, minPed, dataPedestal, dataADCmap)

def findExpectedX(point1, point2, y3):
    x3 = point1[0]
    if point2[0] - point1[0] != 0:
        m = (point2[1] - point1[1]) / (point2[0] - point1[0])
        if m != 0:
            x3 = (y3 - point1[1]) / m + point1[0]
    expectedPoint = attrdict(x3=x3, y3=y3)
    return expectedPoint
# end of findExpectedX

def arePointsAlmostCollinear(event, point1, point2, point3):
    m = 0
    x3 = point3[0]
    if (point2[0] - point1[0]) != 0:
        m = (point2[1] - point1[1]) / (point2[0] - point1[0])
        if m != 0:
            x3 = (point3[1] - point1[1]) / m + point1[0]
    lowerBound = x3 - pointTolerance
    upperBound = x3 + pointTolerance
    if point3[0] >= lowerBound and point3[0] <= upperBound:
        return True
    else:
        return False
# end of arePointsAlmostCollinear

def analyzeTracking(event, arr, numberofplanes1, numberofplanes2):
    global tracking6MiddleMissedXY
    global tracking6MiddleMissedX
    global tracking6MiddleMissedY
    global tracking6MiddleHitsXsingleBothLayers
    global tracking6MiddleHitsXsingleTopBottom
    global tracking6MiddleHitsYsingleTopBottom
    global tracking6MiddleHitsXY
    global tracking6MiddleHitsOnlyX
    global tracking6MiddleHitsOnlyY
    global tracking5TopMissingX
    global tracking5MiddleMissingX
    global tracking5BottomMissingX
    global tracking5TopMissingY
    global tracking5MiddleMissingY
    global tracking5BottomMissingY
    global tracking4TopMissing
    global tracking4MiddleMissing
    global tracking4BottomMissing

    g = globals()
    if 'eventFilter6' not in g:
        g['eventFilter6'] = []
    if 'eventFilter5' not in g:
        g['eventFilter5'] = []
    if 'eventFilter4' not in g:
        g['eventFilter4'] = []

    # collect x layer points first and y layer next, always top to bottom
    points = [None] * (len(arr) * 3)
    xLayerHitCount = []
    yLayerHitCount = []

    for i, plane in enumerate(arr):
        p = i * 3
        points[p] = plane[2]
        points[p + 1] = plane[3]
        points[p + 2] = plane[4]

    if len(arr) > 1:
        xLayerHitCount.append(arr[0][5])
        xLayerHitCount.append(arr[0][6])
        yLayerHitCount.append(arr[1][5])
        yLayerHitCount.append(arr[1][6])

    pointCount = 0
    for pt in points:
        #if pt is not None and len(pt) >= 2 and pt[0] is not None and pt[1] is not None:
        valid = False
        try:
            if pt is not None and pt[0] is not None and pt[1] is not None:
                valid = True
        except:
            valid = False

        if valid:
            pointCount += 1


    allPointsInLineX = True
    allPointsInLineY = True

    if pointCount == 6:
        allPointsInLineX = arePointsAlmostCollinear(event, points[0], points[2], points[1])
        allPointsInLineY = arePointsAlmostCollinear(event, points[3], points[5], points[4])

        if allPointsInLineX is False and allPointsInLineY is False:
            expectedPointX = findExpectedX(points[0], points[2], points[1][1])
            expectedPointY = findExpectedX(points[3], points[5], points[4][1])
            tracking6MiddleMissedXY.append([event, points, expectedPointX, expectedPointY])

        elif allPointsInLineX is False:
            expectedPoint = findExpectedX(points[0], points[2], points[1][1])
            tracking6MiddleMissedX.append([event, points, expectedPoint])

        elif allPointsInLineY is False:
            expectedPoint = findExpectedX(points[3], points[5], points[4][1])
            tracking6MiddleMissedY.append([event, points, expectedPoint])

        if allPointsInLineX and allPointsInLineY:
            # X and Y layer: test if there is only one top and bottom hit
            if (xLayerHitCount[0] == 1 and xLayerHitCount[1] == 1 and
                    yLayerHitCount[0] == 1 and yLayerHitCount[1] == 1):
                tracking6MiddleHitsXsingleBothLayers.append([event, points])

            elif xLayerHitCount[0] == 1 and xLayerHitCount[1] == 1:
                tracking6MiddleHitsXsingleTopBottom.append([event, points])

            elif yLayerHitCount[0] == 1 and yLayerHitCount[1] == 1:
                tracking6MiddleHitsYsingleTopBottom.append([event, points])

            expectedPointX = findExpectedX(points[0], points[2], points[1][1])
            expectedPointY = findExpectedX(points[3], points[5], points[4][1])
            tracking6MiddleHitsXY.append([event, points, expectedPointX, expectedPointY])
            g['eventFilter6'].append(event + 1)

        if allPointsInLineX is True:
            expectedPointX = findExpectedX(points[0], points[2], points[1][1])
            tracking6MiddleHitsOnlyX.append([event, points, expectedPointX])

        if allPointsInLineY is True:
            expectedPointY = findExpectedX(points[3], points[5], points[4][1])
            tracking6MiddleHitsOnlyY.append([event, points, expectedPointY])

    missingPointNdx = -1

    # 5-plane case
    if pointCount == numberofplanes1 or allPointsInLineX is False or allPointsInLineY is False:
        for i, pt in enumerate(points):
            if pt is None or len(pt) < 2 or pt[0] is None:
                missingPointNdx = i

        if missingPointNdx == 0:
            y3 = layerOrderX[2][0]
            expectedPoint = findExpectedX(points[1], points[2], y3)
            tracking5TopMissingX.append([event, points, expectedPoint])

        elif missingPointNdx == 1:
            y3 = layerOrderX[1][0]
            expectedPoint = findExpectedX(points[2], points[0], y3)
            tracking5MiddleMissingX.append([event, points, expectedPoint])

        elif missingPointNdx == 2:
            y3 = layerOrderX[0][0]
            expectedPoint = findExpectedX(points[1], points[0], y3)
            tracking5BottomMissingX.append([event, points, expectedPoint])

        elif missingPointNdx == 3:
            y3 = layerOrderY[2][0]
            expectedPoint = findExpectedX(points[4], points[5], y3)
            tracking5TopMissingY.append([event, points, expectedPoint])

        elif missingPointNdx == 4:
            y3 = layerOrderY[1][0]
            expectedPoint = findExpectedX(points[3], points[5], y3)
            tracking5MiddleMissingY.append([event, points, expectedPoint])

        elif missingPointNdx == 5:
            y3 = layerOrderY[0][0]
            expectedPoint = findExpectedX(points[3], points[4], y3)
            tracking5BottomMissingY.append([event, points, expectedPoint])

        g['eventFilter5'].append(event + 1)

    # 4-plane case
    if pointCount == numberofplanes2:
        countMissing = 0
        indicesUndef = []

        for i, pt in enumerate(points):
            if pt is None or len(pt) < 2 or pt[0] is None:
                countMissing += 1
                indicesUndef.append(i)

        if countMissing == 2:
            firstMissing = indicesUndef[0]
            secondMissing = indicesUndef[1]

            if firstMissing == 0 and secondMissing == 3:
                y3 = layerOrderX[2][0]
                xExpectedPoint = findExpectedX(points[1], points[2], y3)
                y3 = layerOrderY[2][0]
                yExpectedPoint = findExpectedX(points[4], points[5], y3)
                tracking4TopMissing.append([event, xExpectedPoint, yExpectedPoint])
                g['eventFilter4'].append(event + 1)

            if firstMissing == 1 and secondMissing == 4:
                y3 = layerOrderX[1][0]
                xExpectedPoint = findExpectedX(points[2], points[0], y3)
                y3 = layerOrderY[1][0]
                yExpectedPoint = findExpectedX(points[3], points[5], y3)
                tracking4MiddleMissing.append([event, xExpectedPoint, yExpectedPoint])
                g['eventFilter4'].append(event + 1)

            if firstMissing == 2 and secondMissing == 5:
                y3 = layerOrderX[0][0]
                xExpectedPoint = findExpectedX(points[1], points[0], y3)
                y3 = layerOrderY[0][0]
                yExpectedPoint = findExpectedX(points[3], points[4], y3)
                tracking4BottomMissing.append([event, xExpectedPoint, yExpectedPoint])
                g['eventFilter4'].append(event + 1)
# end of analyzeTracking

size = 35.0
pedThreshold = 10
totalIntensity = 300
pointWidth = 1.0  # 2.0 cm
layerAct = [[] for x in range(3)]
layerQuad = [[] for x in range(3)]
layerQuadSize = [[] for x in range(3)]
layerTriangle = [[] for x in range(3)]
eventChannels = [[] for x in range(3)]
microMinute = 60000000

class attrdict(dict):
    def __init__(self, *args, **kwargs):
        dict.__init__(self, *args, **kwargs)
        self.__dict__ = self
#end of attrdict

def getAnalysisIndexesOfTwoHighest(arr):
    """
    Returns indices of the two highest values in descending value order.
    """
    if len(arr) == 0:
        return []
    if len(arr) == 1:
        return [0]

    max1 = float('-inf')
    max2 = float('-inf')
    idx1 = -1
    idx2 = -1

    for i, v in enumerate(arr):
        if v > max1:
            max2, idx2 = max1, idx1
            max1, idx1 = v, i
        elif v > max2:
            max2, idx2 = v, i

    if idx1 != -1 and idx2 != -1:
        return [idx1, idx2]
    if idx1 != -1:
        return [idx1]
    return []
#end of getAnalysisIndexesOfTwoHighest

def getAnalysisSingleSidePoint(layerStart, event, layerTriangle, eventChannels, channelNdx, layer, zValue,
                               overallCellSize):
    sidePoint = attrdict()
    addOn = 0.0
    # print(layerStart[layer])
    if layerStart[layer] == 'Pyramid':
        addOn = 1.0
    x1 = layerTriangle[2][0]
    x2 = layerTriangle[3][0]
    x3 = layerTriangle[4][0]
    # print(x1,x2,x3, overallCellSize)
    x = (((x1 + x2 + x3) / 3.0) / (overallCellSize / 2.0)) + addOn
    x = x * pointWidth
    y = zValue
    yProjected = (y / (overallCellSize / 2.0)) + addOn
    channel1 = -1
    channel2 = -1
    if len(eventChannels[layer]) > 0:
        channel1 = eventChannels[layer][channelNdx]
    # if event < 2:
    #	print(event,"single: ", x)
    sidePoint = attrdict(x=x, y=y, yProjected=yProjected, channel1=channel1, channel2=channel2)
    return sidePoint
# end of getAnalysisSingleSidePoint

def calculateAnalysisPointByPercentage(layerStart, event, x1, y1, x2, y2, percentage, yProjected, eventChannels, ndx,
                                       layer, zValue, neighbors, overallCellSize):
    dx = x2 - x1
    dy = y2 - y1
    addOn = 0.0
    if layerStart[layer] == 'Pyramid':
        addOn = 1.0
    x = ((x1 + (dx * percentage / 100.0)) / (overallCellSize / 2.0)) + addOn
    x = x * pointWidth
    y = zValue
    channel1 = -1
    channel2 = -1
    # Match JS behavior: if neighbor indices are provided, map back to eventChannels
    # using the neighbor indices. Fall back to using ndx/ndx+1 when neighbors
    # are not available or invalid.
    try:
        if isinstance(neighbors, (list, tuple)) and len(neighbors) > 1:
            n0 = neighbors[0]
            n1 = neighbors[1]
            # ensure eventChannels for layer exists
            if layer < len(eventChannels) and isinstance(eventChannels[layer], (list, tuple)):
                if n0 < n1:
                    if n0 < len(eventChannels[layer]):
                        channel1 = eventChannels[layer][n0]
                    if n1 < len(eventChannels[layer]):
                        channel2 = eventChannels[layer][n1]
                else:
                    if n1 < len(eventChannels[layer]):
                        channel1 = eventChannels[layer][n1]
                    if n0 < len(eventChannels[layer]):
                        channel2 = eventChannels[layer][n0]
        else:
            # legacy fallback (use ndx and ndx+1)
            if layer < len(eventChannels) and isinstance(eventChannels[layer], (list, tuple)):
                if ndx < len(eventChannels[layer]):
                    channel1 = eventChannels[layer][ndx]
                if ndx + 1 < len(eventChannels[layer]):
                    channel2 = eventChannels[layer][ndx + 1]
    except Exception:
        # keep default -1 values on any unexpected error
        channel1 = -1
        channel2 = -1
    # if event < 2:
    #	print(event,"percentage: ", x)
    sidePoint = attrdict(x=x, y=y, yProjected=yProjected, channel1=channel1, channel2=channel2)
    return sidePoint
# end of calculateAnalysisPointbyPercentage

def areNeighborsIn(neighbors, length):
    for n in neighbors:
        if n >= length:
            return False
    return True
# end of areNeighborsIn

def analyzeAnalysisCluster(event, x, arr, howmany):
    ndx = []
    intensities = []
    # keep original arr indices for each pushed intensity so we can map back
    intensity_indices = []
    lastX = 0

    if len(arr) - x == 2 and (arr[len(arr) - 1][0] - arr[len(arr) - 2][0] <= 35.0):
        intensities.append(arr[len(arr) - 2][1])
        intensity_indices.append(len(arr) - 2)
        intensities.append(arr[len(arr) - 1][1])
        intensity_indices.append(len(arr) - 1)
    else:
        for i in range(x, len(arr) - 1):
            if arr[i + 1][0] - arr[i][0] < 35.0 and len(intensities) < 2:
                intensities.append(arr[i][1])
                intensity_indices.append(i)
                intensities.append(arr[i + 1][1])
                intensity_indices.append(i + 1)
            lastX = i

        # deal with one more item
        if len(arr) >= lastX and lastX >= 1 and len(intensities) < 2:
            if arr[lastX][0] - arr[lastX - 1][0] < 35.0:
                intensities.append(arr[lastX][1])

    ndx = getAnalysisIndexesOfTwoHighest(intensities)
    # map returned indices (into intensities list) back to original arr indices
    for i in range(len(ndx)):
        ia = ndx[i]
        if ia < len(intensity_indices):
            ndx[i] = intensity_indices[ia]
        else:
            # fallback to previous behaviour
            ndx[i] += x

    return ndx

# Keep backward compatibility with the typoed name already used elsewhere
def analyzeAnalyisCluster(event, x, arr, howmany):
    return analyzeAnalysisCluster(event, x, arr, howmany)
# en of analyzeAnalysisCluster

def getAnalysisSidePointFromNeighbors(layerStart, event, x, layerTriangle, layerAct, layer, eventChannels, zValue,
                                      howmany, overallCellSize):
    sidePoint = attrdict()
    yProjected = 0
    x1 = 0
    y1 = 0
    x2 = 0
    y2 = 0
    point1Intensity = 0
    point2Intensity = 0

    neighbors = analyzeAnalysisCluster(event, x, layerAct[layer], howmany)

    if len(neighbors) > 1 and neighbors[0] > -1 and neighbors[1] > -1 and areNeighborsIn(neighbors, len(layerTriangle[layer])):
        if neighbors[0] < neighbors[1]:
            x1 = layerTriangle[layer][neighbors[0]][3][0]
            y1 = layerTriangle[layer][neighbors[0]][3][1]
            x2 = layerTriangle[layer][neighbors[0]][4][0]
            y2 = layerTriangle[layer][neighbors[0]][4][1]
            yProjected = layerTriangle[layer][neighbors[0]][5]
            point1Intensity = layerTriangle[layer][neighbors[0]][1]
            point2Intensity = layerTriangle[layer][neighbors[1]][1]
        else:
            x1 = layerTriangle[layer][neighbors[1]][3][0]
            y1 = layerTriangle[layer][neighbors[1]][3][1]
            x2 = layerTriangle[layer][neighbors[1]][4][0]
            y2 = layerTriangle[layer][neighbors[1]][4][1]
            yProjected = layerTriangle[layer][neighbors[1]][5]
            point1Intensity = layerTriangle[layer][neighbors[1]][1]
            point2Intensity = layerTriangle[layer][neighbors[0]][1]

        pointPercentSum = point1Intensity + point2Intensity
        pointPercent = 0.0
        if pointPercentSum != 0:
            pointPercent = point1Intensity * 100.0 / pointPercentSum

        sidePoint = calculateAnalysisPointByPercentage(
            layerStart, event, x1, y1, x2, y2, pointPercent, yProjected,
            eventChannels, x, layer, zValue, neighbors, overallCellSize
        )

    return sidePoint
# end of getAnalysisSidePointFromNeighbors

def isPointInGroup(point, pointGroup):
    found = False
    for i in range(len(pointGroup)):
        if len(point) > 0 and len(pointGroup[i]) > 0:
            if pointGroup[i].x == point.x and pointGroup[i].y == point.y:
                found = True
    return found
#end of isPointInGroup

def calculateAnalysisSidePoint(layerStart, event, layerAct, layerTriangle, eventChannels, layer, zValue,
                               overallCellSize):
    sidePointGroup = []

    if len(layerTriangle[layer]) > 0:
        x = 0
        while x < len(layerTriangle[layer]):
            # determine contiguous cluster size starting at x
            if len(layerAct[layer]) == 1:
                channelClusterCount = 1
            else:
                channelClusterCount = 0
                done = False
                for i in range(x, len(layerAct[layer]) - 1):
                    if layerAct[layer][i + 1][0] - layerAct[layer][i][0] < 35.0 and done is False:
                        channelClusterCount += 1
                    else:
                        done = True
                channelClusterCount += 1

            if channelClusterCount == 1:
                sidePoint = getAnalysisSingleSidePoint(
                    layerStart, event, layerTriangle[layer][x], eventChannels, x, layer, zValue, overallCellSize
                )
                sidePointGroup.append(sidePoint)

            elif channelClusterCount == 2:
                sidePoint = getAnalysisSidePointFromNeighbors(
                    layerStart, event, x, layerTriangle, layerAct, layer, eventChannels, zValue,
                    channelClusterCount, overallCellSize
                )
                if len(sidePoint) > 0 and not isPointInGroup(sidePoint, sidePointGroup):
                    sidePointGroup.append(sidePoint)
                x += 1

            else:
                # cluster greater than 2
                for j in range(x, channelClusterCount + x):
                    sidePoint = getAnalysisSidePointFromNeighbors(
                        layerStart, event, j, layerTriangle, layerAct, layer, eventChannels, zValue,
                        channelClusterCount, overallCellSize
                    )
                    if len(sidePoint) > 0 and not isPointInGroup(sidePoint, sidePointGroup):
                        sidePointGroup.append(sidePoint)
                x += channelClusterCount - 1

            x += 1

    return [value for value in sidePointGroup if len(value) > 0]

# end of calculateAnalysisSidePoint

def checkCalculatedX(point1, point2, y3):
    x3 = point1.x
    if (point2.x - point1.x) != 0:
        m = (point2.y - point1.y) / (point2.x - point1.x)
        if m != 0:
            x3 = (y3.y - point1.y) / m + point1.x
    return attrdict(x=x3, y=y3.y)

# end of checkCalculatedX

investigatePlanes = []
dx = []
dy = []
dxbottommiddle = []
dybottommiddle = []
dxtopmiddle = []
dytopmiddle = []
# Records of events where side-point candidates were removed by channel-range filters.
# Each entry is a dict: { 'event': int, 'layer': 'X'|'Y', 'board': int, 'plane_pos': 0|1|2, 'removed': [ (chan1, chan2), ... ] }
filtered_out_by_range = []
# Records of events where side-point candidates were ACCEPTED by channel-range filters.
# Each entry is a dict: { 'event': int, 'layer': 'X'|'Y', 'board': int, 'plane_pos': 0|1|2, 'accepted': [ (chan1, chan2), ... ] }
accepted_by_range = []


def calculateAnalysisTrack(whichLayer, event, layerAct, layerQuad, layerQuadSize, layerTriangle, layerOrder,
                           eventChannels, layerStart, overallCellSize,
                           x_ranges=None, y_ranges=None):
    global dx
    global dy
    global dxbottommiddle
    global dybottommiddle
    global dxtopmiddle
    global dytopmiddle
    global investigatePlanes
    global filtered_out_by_range

    sidePointX1 = calculateAnalysisSidePoint(layerStart, event, layerAct, layerTriangle, eventChannels,
                                             layerOrder[0][2], layerOrder[0][0], overallCellSize)
    sidePointX2 = calculateAnalysisSidePoint(layerStart, event, layerAct, layerTriangle, eventChannels,
                                             layerOrder[1][2], layerOrder[1][0], overallCellSize)
    sidePointX3 = calculateAnalysisSidePoint(layerStart, event, layerAct, layerTriangle, eventChannels,
                                             layerOrder[2][2], layerOrder[2][0], overallCellSize)

    def _filter_sidepoints_for_range(sidepoints, ch_range):
        if not ch_range:
            return sidepoints
        ch_min, ch_max = ch_range
        filtered = []
        for p in sidepoints:
            c1 = getattr(p, 'channel1', -1)
            c2 = getattr(p, 'channel2', -1)
            if (c1 != -1 and ch_min <= c1 <= ch_max) or (c2 != -1 and ch_min <= c2 <= ch_max):
                filtered.append(p)
        return filtered
    if whichLayer == 'X' and x_ranges:
        # plane 0 (bottom)
        _orig = sidePointX1
        _ch_range = x_ranges[layerOrder[0][2]] if len(x_ranges) > 0 else None
        sidePointX1 = _filter_sidepoints_for_range(sidePointX1, _ch_range)
        # record accepted points when a channel range was applied for this board
        try:
            if _ch_range is not None:
                accepted = []
                for p in sidePointX1:
                    accepted.append((getattr(p, 'channel1', -1), getattr(p, 'channel2', -1)))
                accepted_by_range.append({'event': event, 'layer': whichLayer, 'board': layerOrder[0][2], 'plane_pos': 0, 'accepted': accepted})
        except Exception:
            pass
        if len(sidePointX1) < len(_orig):
            removed = []
            for p in _orig:
                if p not in sidePointX1:
                    removed.append((getattr(p, 'channel1', -1), getattr(p, 'channel2', -1)))
            try:
                filtered_out_by_range.append({'event': event, 'layer': whichLayer, 'board': layerOrder[0][2], 'plane_pos': 0, 'removed': removed})
            except Exception:
                pass
        # plane 1 (middle)
        _orig = sidePointX2
        _ch_range = x_ranges[layerOrder[1][2]] if len(x_ranges) > 1 else None
        sidePointX2 = _filter_sidepoints_for_range(sidePointX2, _ch_range)
        try:
            if _ch_range is not None:
                accepted = []
                for p in sidePointX2:
                    accepted.append((getattr(p, 'channel1', -1), getattr(p, 'channel2', -1)))
                accepted_by_range.append({'event': event, 'layer': whichLayer, 'board': layerOrder[1][2], 'plane_pos': 1, 'accepted': accepted})
        except Exception:
            pass
        if len(sidePointX2) < len(_orig):
            removed = []
            for p in _orig:
                if p not in sidePointX2:
                    removed.append((getattr(p, 'channel1', -1), getattr(p, 'channel2', -1)))
            try:
                filtered_out_by_range.append({'event': event, 'layer': whichLayer, 'board': layerOrder[1][2], 'plane_pos': 1, 'removed': removed})
            except Exception:
                pass
        # plane 2 (top)
        _orig = sidePointX3
        _ch_range = x_ranges[layerOrder[2][2]] if len(x_ranges) > 2 else None
        sidePointX3 = _filter_sidepoints_for_range(sidePointX3, _ch_range)
        try:
            if _ch_range is not None:
                accepted = []
                for p in sidePointX3:
                    accepted.append((getattr(p, 'channel1', -1), getattr(p, 'channel2', -1)))
                accepted_by_range.append({'event': event, 'layer': whichLayer, 'board': layerOrder[2][2], 'plane_pos': 2, 'accepted': accepted})
        except Exception:
            pass
        if len(sidePointX3) < len(_orig):
            removed = []
            for p in _orig:
                if p not in sidePointX3:
                    removed.append((getattr(p, 'channel1', -1), getattr(p, 'channel2', -1)))
            try:
                filtered_out_by_range.append({'event': event, 'layer': whichLayer, 'board': layerOrder[2][2], 'plane_pos': 2, 'removed': removed})
            except Exception:
                pass
        #if event < 2:
        #    print(event, whichLayer, y_ranges[layerOrder[0][2]], layerOrder)
        #    print(sidePointX1)
        #    print(sidePointX2)
        #    print(sidePointX3)
    elif whichLayer == 'Y' and y_ranges:
        # plane 0 (bottom)
        _orig = sidePointX1
        _ch_range = y_ranges[layerOrder[0][2]] if len(y_ranges) > 0 else None
        sidePointX1 = _filter_sidepoints_for_range(sidePointX1, _ch_range)
        try:
            if _ch_range is not None:
                accepted = []
                for p in sidePointX1:
                    accepted.append((getattr(p, 'channel1', -1), getattr(p, 'channel2', -1)))
                accepted_by_range.append({'event': event, 'layer': whichLayer, 'board': layerOrder[0][2], 'plane_pos': 0, 'accepted': accepted})
        except Exception:
            pass
        if len(sidePointX1) < len(_orig):
            removed = []
            for p in _orig:
                if p not in sidePointX1:
                    removed.append((getattr(p, 'channel1', -1), getattr(p, 'channel2', -1)))
            try:
                filtered_out_by_range.append({'event': event, 'layer': whichLayer, 'board': layerOrder[0][2], 'plane_pos': 0, 'removed': removed})
            except Exception:
                pass
        # plane 1 (middle)
        _orig = sidePointX2
        _ch_range = y_ranges[layerOrder[1][2]] if len(y_ranges) > 1 else None
        sidePointX2 = _filter_sidepoints_for_range(sidePointX2, _ch_range)
        try:
            if _ch_range is not None:
                accepted = []
                for p in sidePointX2:
                    accepted.append((getattr(p, 'channel1', -1), getattr(p, 'channel2', -1)))
                accepted_by_range.append({'event': event, 'layer': whichLayer, 'board': layerOrder[1][2], 'plane_pos': 1, 'accepted': accepted})
        except Exception:
            pass
        if len(sidePointX2) < len(_orig):
            removed = []
            for p in _orig:
                if p not in sidePointX2:
                    removed.append((getattr(p, 'channel1', -1), getattr(p, 'channel2', -1)))
            try:
                filtered_out_by_range.append({'event': event, 'layer': whichLayer, 'board': layerOrder[1][2], 'plane_pos': 1, 'removed': removed})
            except Exception:
                pass
        # plane 2 (top)
        _orig = sidePointX3
        _ch_range = y_ranges[layerOrder[2][2]] if len(y_ranges) > 2 else None
        sidePointX3 = _filter_sidepoints_for_range(sidePointX3, _ch_range)
        try:
            if _ch_range is not None:
                accepted = []
                for p in sidePointX3:
                    accepted.append((getattr(p, 'channel1', -1), getattr(p, 'channel2', -1)))
                accepted_by_range.append({'event': event, 'layer': whichLayer, 'board': layerOrder[2][2], 'plane_pos': 2, 'accepted': accepted})
        except Exception:
            pass
        if len(sidePointX3) < len(_orig):
            removed = []
            for p in _orig:
                if p not in sidePointX3:
                    removed.append((getattr(p, 'channel1', -1), getattr(p, 'channel2', -1)))
            try:
                filtered_out_by_range.append({'event': event, 'layer': whichLayer, 'board': layerOrder[2][2], 'plane_pos': 2, 'removed': removed})
            except Exception:
                pass
        #if event < 2:
            #print(event, whichLayer, y_ranges[layerOrder[0][2]], layerOrder)
            #print(sidePointX1)
            #print(sidePointX2)
            #print(sidePointX3)
    pointX1 = attrdict(x=None, y=None, yProjected=None, channel1=-1, channel2=-1)
    pointX2 = attrdict(x=None, y=None, yProjected=None, channel1=-1, channel2=-1)
    pointX3 = attrdict(x=None, y=None, yProjected=None, channel1=-1, channel2=-1)

    if len(sidePointX1) > 0:
        pointX1 = sidePointX1[0]
    if len(sidePointX2) > 0:
        pointX2 = sidePointX2[0]
    if len(sidePointX3) > 0:
        pointX3 = sidePointX3[0]

    tempX1 = attrdict(x=None, y=None, yProjected=None, channel1=-1, channel2=-1)
    tempX2 = attrdict(x=None, y=None, yProjected=None, channel1=-1, channel2=-1)
    tempX3 = attrdict(x=None, y=None, yProjected=None, channel1=-1, channel2=-1)

    diff = 1000.0

    # determine best track for all the data analysis
    if len(sidePointX2) > 0:
        if len(sidePointX1) > 0 and len(sidePointX3) > 0:
            for middlePoint in sidePointX2:
                # test 1
                if len(sidePointX1) == 1 and len(sidePointX3) == 1:
                    expectedMiddlePoint = checkCalculatedX(sidePointX1[0], sidePointX3[0], middlePoint)
                    if abs(middlePoint.x - expectedMiddlePoint.x) < diff:
                        diff = abs(middlePoint.x - expectedMiddlePoint.x)
                        tempX1 = sidePointX1[0]
                        tempX2 = middlePoint
                        tempX3 = sidePointX3[0]
                        if getattr(tempX1, 'x', None) is not None and (getattr(pointX1, 'x', None) != getattr(tempX1, 'x', None)):
                            pointX1 = tempX1
                        if getattr(tempX2, 'x', None) is not None and (getattr(pointX2, 'x', None) != getattr(tempX2, 'x', None)):
                            pointX2 = tempX2
                        if getattr(tempX3, 'x', None) is not None and (getattr(pointX3, 'x', None) != getattr(tempX3, 'x', None)):
                            pointX3 = tempX3

                # test 2
                if len(sidePointX3) > 1 and len(sidePointX1) == 1:
                    for j in range(len(sidePointX3)):
                        expectedMiddlePoint = checkCalculatedX(sidePointX1[0], sidePointX3[j], middlePoint)
                        if abs(middlePoint.x - expectedMiddlePoint.x) < diff:
                            diff = abs(middlePoint.x - expectedMiddlePoint.x)
                            tempX1 = sidePointX1[0]
                            tempX2 = middlePoint
                            tempX3 = sidePointX3[j]
                            if getattr(tempX1, 'x', None) is not None and (getattr(pointX1, 'x', None) != getattr(tempX1, 'x', None)):
                                pointX1 = tempX1
                            if getattr(tempX2, 'x', None) is not None and (getattr(pointX2, 'x', None) != getattr(tempX2, 'x', None)):
                                pointX2 = tempX2
                            if getattr(tempX3, 'x', None) is not None and (getattr(pointX3, 'x', None) != getattr(tempX3, 'x', None)):
                                pointX3 = tempX3

                # test 3
                if len(sidePointX1) > 1 and len(sidePointX3) == 1:
                    for j in range(len(sidePointX1)):
                        expectedMiddlePoint = checkCalculatedX(sidePointX1[j], sidePointX3[0], middlePoint)
                        if abs(middlePoint.x - expectedMiddlePoint.x) < diff:
                            diff = abs(middlePoint.x - expectedMiddlePoint.x)
                            tempX1 = sidePointX1[j]
                            tempX2 = middlePoint
                            tempX3 = sidePointX3[0]
                            if getattr(tempX1, 'x', None) is not None and (getattr(pointX1, 'x', None) != getattr(tempX1, 'x', None)):
                                pointX1 = tempX1
                            if getattr(tempX2, 'x', None) is not None and (getattr(pointX2, 'x', None) != getattr(tempX2, 'x', None)):
                                pointX2 = tempX2
                            if getattr(tempX3, 'x', None) is not None and (getattr(pointX3, 'x', None) != getattr(tempX3, 'x', None)):
                                pointX3 = tempX3

                # test 4
                if len(sidePointX1) > 1 and len(sidePointX3) > 1:
                    for j in range(len(sidePointX1)):
                        for k in range(len(sidePointX3)):
                            expectedMiddlePoint = checkCalculatedX(sidePointX1[j], sidePointX3[k], middlePoint)
                            if abs(middlePoint.x - expectedMiddlePoint.x) < diff:
                                diff = abs(middlePoint.x - expectedMiddlePoint.x)
                                tempX1 = sidePointX1[j]
                                tempX2 = middlePoint
                                tempX3 = sidePointX3[k]
                                if getattr(tempX1, 'x', None) is not None and (getattr(pointX1, 'x', None) != getattr(tempX1, 'x', None)):
                                    pointX1 = tempX1
                                if getattr(tempX2, 'x', None) is not None and (getattr(pointX2, 'x', None) != getattr(tempX2, 'x', None)):
                                    pointX2 = tempX2
                                if getattr(tempX3, 'x', None) is not None and (getattr(pointX3, 'x', None) != getattr(tempX3, 'x', None)):
                                    pointX3 = tempX3

    # investigate tracking
    xTopPoint = [None, None]
    xMiddlePoint = [None, None]
    xBottomPoint = [None, None]
    yTopPoint = [None, None]
    yMiddlePoint = [None, None]
    yBottomPoint = [None, None]

    if whichLayer == 'X':
        xTopPoint = [pointX3.x, pointX3.y]
        xMiddlePoint = [pointX2.x, pointX2.y]
        xBottomPoint = [pointX1.x, pointX1.y]
        investigatePlanes.append(['X', event, xTopPoint, xMiddlePoint, xBottomPoint,
                                  len(layerAct[2]), len(layerAct[0])])
    else:
        yTopPoint = [pointX3.x, pointX3.y]
        yMiddlePoint = [pointX2.x, pointX2.y]
        yBottomPoint = [pointX1.x, pointX1.y]
        investigatePlanes.append(['Y', event, yTopPoint, yMiddlePoint, yBottomPoint,
                                  len(layerAct[2]), len(layerAct[0])])

        if len(investigatePlanes) >= 2:
            analyzeTracking(event, investigatePlanes, 5, 4)
            investigatePlanes = []

    # populate dx/dy or partial track arrays
    if pointX1.x is not None and pointX1.x > 0 and pointX3.x is not None and pointX3.x > 0:
        deltax = pointX3.x - pointX1.x
        deltaz = pointX3.y - pointX1.y
        deltaxTM = 0.0
        deltazTM = 0.0

        if pointX2.x is not None and pointX2.x > 0:
            deltaxTM = pointX3.x - pointX2.x
            deltazTM = pointX3.y - pointX2.y

        if whichLayer == 'X':
            dx.append([event, pointX1, pointX2, pointX3, deltax, deltaz, deltaxTM, deltazTM])
        else:
            dy.append([event, pointX1, pointX2, pointX3, deltax, deltaz, deltaxTM, deltazTM])

    else:
        if pointX1.x is not None and pointX1.x > 0 and pointX2.x is not None and pointX2.x > 0:
            deltax = pointX2.x - pointX1.x
            deltaz = pointX2.y - pointX1.y
            if whichLayer == 'X':
                dxbottommiddle.append([event, pointX1, pointX2, pointX3, deltax, deltaz])
            else:
                dybottommiddle.append([event, pointX1, pointX2, pointX3, deltax, deltaz])

        else:
            if pointX2.x is not None and pointX2.x > 0 and pointX3.x is not None and pointX3.x > 0:
                deltax = pointX3.x - pointX2.x
                deltaz = pointX3.y - pointX2.y
                if whichLayer == 'X':
                    dxtopmiddle.append([event, pointX1, pointX2, pointX3, deltax, deltaz])
                else:
                    dytopmiddle.append([event, pointX1, pointX2, pointX3, deltax, deltaz])
# end of calculateAnalysisTrack

def calculateAnalysisTriangle(dir, xpos, y, channel, inten, quadMember):
    triangleCoords = []
    triangleCoords.append(dir)
    triangleCoords.append(inten)
    triangleCoords.append([xpos, y])
    triangleCoords.append([xpos + size, y])
    y3 = 0
    height = 0
    if dir:
        y3 = y - (math.sqrt(3) * size / 2.0)
        height = y - ((math.sqrt(3) * size / 2.0) / 2.0)
        triangleCoords.append([xpos + (size / 2.0), y3])
    else:
        y3 = y + (math.sqrt(3) * size / 2.0)
        height = y + ((math.sqrt(3) * size / 2.0) / 2.0)
        triangleCoords.append([xpos + (size / 2.0), y3])
    triangleCoords.append(height)
    triangleCoords.append(quadMember)
    return triangleCoords
# end of calculateAnalysisTriangle

def calculateAnalysisQuad(event, layer, up, xp, yp, channel, layerAct, reversed, numQuads, coordArray, ped, layerQuad,
                          quadMember, layerQuadSize, cellSize, quadGap, layerTriangle, eventChannels):
    adcChannel = 0
    pedPosition = 0
    triangleCoords = []
    if up:
        if reversed:
            # need to reverse the channels
            channelPosition = (numQuads * 4) - channel - 1
            adcChannel = coordArray[event][layer][channelPosition][0]
            pedPosition = (numQuads * 4) - channelPosition
            if up:
                triangleCoords = calculateAnalysisTriangle(True, xp - (cellSize / 2) + 1, yp + cellSize - 5, adcChannel,
                                                           ped[event][layer][channelPosition] / totalIntensity,
                                                           quadMember)
            else:
                triangleCoords = calculateAnalysisTriangle(True, xp + (cellSize / 2) + 1, yp + cellSize - 5, adcChannel,
                                                           ped[event][layer][channelPosition] / totalIntensity,
                                                           quadMember)
            if ped[event][layer][channelPosition] > pedThreshold:
                if up:
                    layerAct[layer].append([xp - (cellSize / 2), ped[event][layer][channelPosition]])
                else:
                    layerAct[layer].append([xp + (cellSize / 2), ped[event][layer][channelPosition]])
                layerQuad[layer].append([quadMember, ped[event][layer][channelPosition]])
                layerQuadSize[layer].append([cellSize, quadGap])
                layerTriangle[layer].append(triangleCoords)
                eventChannels[layer].append(adcChannel)
        else:
            adcChannel = coordArray[event][layer][channel][0]
            #if event < 5:
            #    print(event, layer, coordArray[event][layer][channel])
            if up:
                triangleCoords = calculateAnalysisTriangle(True, xp - (cellSize / 2) + 1, yp + cellSize - 5, adcChannel,
                                                           ped[event][layer][channel] / totalIntensity, quadMember)
            else:
                triangleCoords = calculateAnalysisTriangle(True, xp + (cellSize / 2) + 1, yp + cellSize - 5, adcChannel,
                                                           ped[event][layer][channel] / totalIntensity, quadMember)
            if ped[event][layer][channel] > pedThreshold:
                if up:
                    layerAct[layer].append([xp - (cellSize / 2), ped[event][layer][channel]])
                else:
                    layerAct[layer].append([xp + (cellSize / 2), ped[event][layer][channel]])
                layerQuad[layer].append([quadMember, ped[event][layer][channel]])
                layerQuadSize[layer].append([cellSize, quadGap])
                layerTriangle[layer].append(triangleCoords)
                eventChannels[layer].append(adcChannel)
        channel += 1
        if reversed:
            channelPosition = (numQuads * 4) - channel - 1
            adcChannel = coordArray[event][layer][channelPosition][0]
            pedPosition = (numQuads * 4) - channelPosition
            if up:
                triangleCoords = calculateAnalysisTriangle(True, xp - (cellSize / 2) + 1, yp + cellSize - 5, adcChannel,
                                                           ped[event][layer][channelPosition] / totalIntensity,
                                                           quadMember)
            else:
                triangleCoords = calculateAnalysisTriangle(True, xp + (cellSize / 2) + 1, yp + cellSize - 5, adcChannel,
                                                           ped[event][layer][channelPosition] / totalIntensity,
                                                           quadMember)
            if ped[event][layer][channelPosition] > pedThreshold:
                if up:
                    layerAct[layer].append([xp - (cellSize / 2), ped[event][layer][channelPosition]])
                else:
                    layerAct[layer].append([xp + (cellSize / 2), ped[event][layer][channelPosition]])
                layerQuad[layer].append([quadMember, ped[event][layer][channelPosition]])
                layerQuadSize[layer].append([cellSize, quadGap])
                layerTriangle[layer].append(triangleCoords)
                eventChannels[layer].append(adcChannel)
        else:
            adcChannel = coordArray[event][layer][channel][0]
            #if event < 5:
            #    print(event, layer, coordArray[event][layer][channel])
            triangleCoords = calculateAnalysisTriangle(False, xp + 1, yp, adcChannel,
                                                       ped[event][layer][channel] / totalIntensity, quadMember)
            if ped[event][layer][channel] > pedThreshold:
                if up:
                    layerAct[layer].append([xp - (cellSize / 2), ped[event][layer][channel]])
                else:
                    layerAct[layer].append([xp + (cellSize / 2), ped[event][layer][channel]])
                layerQuad[layer].append([quadMember, ped[event][layer][channel]])
                layerQuadSize[layer].append([cellSize, quadGap])
                layerTriangle[layer].append(triangleCoords)
                eventChannels[layer].append(adcChannel)
        channel += 1
    else:
        if reversed:
            channelPosition = (numQuads * 4) - channel - 1
            adcChannel = coordArray[event][layer][channelPosition][0]
            pedPosition = (numQuads * 4) - channelPosition
            if up:
                triangleCoords = calculateAnalysisTriangle(True, xp - (cellSize / 2) + 1, yp + cellSize - 5, adcChannel,
                                                           ped[event][layer][channelPosition] / totalIntensity,
                                                           quadMember)
            else:
                triangleCoords = calculateAnalysisTriangle(True, xp + (cellSize / 2) + 1, yp + cellSize - 5, adcChannel,
                                                           ped[event][layer][channelPosition] / totalIntensity,
                                                           quadMember)
            if ped[event][layer][channelPosition] > pedThreshold:
                if up:
                    layerAct[layer].append([xp - (cellSize / 2), ped[event][layer][channelPosition]])
                else:
                    layerAct[layer].append([xp + (cellSize / 2), ped[event][layer][channelPosition]])
                layerQuad[layer].append([quadMember, ped[event][layer][channelPosition]])
                layerQuadSize[layer].append([cellSize, quadGap])
                layerTriangle[layer].append(triangleCoords)
                eventChannels[layer].append(adcChannel)
        else:
            adcChannel = coordArray[event][layer][channel][0]
            #if event < 5:
            #    print(event, layer, coordArray[event][layer][channel])
            if up:
                triangleCoords = calculateAnalysisTriangle(True, xp - (cellSize / 2) + 1, yp + cellSize - 5, adcChannel,
                                                           ped[event][layer][channel] / totalIntensity, quadMember)
            else:
                triangleCoords = calculateAnalysisTriangle(True, xp + (cellSize / 2) + 1, yp + cellSize - 5, adcChannel,
                                                           ped[event][layer][channel] / totalIntensity, quadMember)
            if ped[event][layer][channel] > pedThreshold:
                if up:
                    layerAct[layer].append([xp - (cellSize / 2), ped[event][layer][channel]])
                else:
                    layerAct[layer].append([xp + (cellSize / 2), ped[event][layer][channel]])
                layerQuad[layer].append([quadMember, ped[event][layer][channel]])
                layerQuadSize[layer].append([cellSize, quadGap])
                layerTriangle[layer].append(triangleCoords)
                eventChannels[layer].append(adcChannel)
        channel += 1
        if reversed:
            channelPosition = (numQuads * 4) - channel - 1
            adcChannel = coordArray[event][layer][channelPosition][0]
            pedPosition = (numQuads * 4) - channelPosition
            if up:
                triangleCoords = calculateAnalysisTriangle(True, xp - (cellSize / 2) + 1, yp + cellSize - 5, adcChannel,
                                                           ped[event][layer][channelPosition] / totalIntensity,
                                                           quadMember)
            else:
                triangleCoords = calculateAnalysisTriangle(True, xp + (cellSize / 2) + 1, yp + cellSize - 5, adcChannel,
                                                           ped[event][layer][channelPosition] / totalIntensity,
                                                           quadMember)
            if ped[event][layer][channelPosition] > pedThreshold:
                if up:
                    layerAct[layer].append([xp - (cellSize / 2), ped[event][layer][channelPosition]])
                else:
                    layerAct[layer].append([xp + (cellSize / 2), ped[event][layer][channelPosition]])
                layerQuad[layer].append([quadMember, ped[event][layer][channelPosition]])
                layerQuadSize[layer].append([cellSize, quadGap])
                layerTriangle[layer].append(triangleCoords)
                eventChannels[layer].append(adcChannel)
        else:
            adcChannel = coordArray[event][layer][channel][0]
            #if event < 5:
            #    print(event, layer, coordArray[event][layer][channel])
            if up:
                triangleCoords = calculateAnalysisTriangle(True, xp - (cellSize / 2) + 1, yp + cellSize - 5, adcChannel,
                                                           ped[event][layer][channel] / totalIntensity, quadMember)
            else:
                triangleCoords = calculateAnalysisTriangle(True, xp + (cellSize / 2) + 1, yp + cellSize - 5, adcChannel,
                                                           ped[event][layer][channel] / totalIntensity, quadMember)
            if ped[event][layer][channel] > pedThreshold:
                if up:
                    layerAct[layer].append([xp - (cellSize / 2), ped[event][layer][channel]])
                else:
                    layerAct[layer].append([xp + (cellSize / 2), ped[event][layer][channel]])
                layerQuad[layer].append([quadMember, ped[event][layer][channel]])
                layerQuadSize[layer].append([cellSize, quadGap])
                layerTriangle[layer].append(triangleCoords)
                eventChannels[layer].append(adcChannel)
        channel += 1
    return channel
# end of calculateAnalysisQuad

def calculateAnalysisLayer(whichLayer, event, layerOrder, x_ranges=None, y_ranges=None):
    channel = 0
    layer = 2
    up = False
    reversed = False
    quadSize = 0.0
    cellSize = 0.0
    quadGap = 0.0
    overallCellSize = 0.0
    startPoint = 0.0

    layerStart = []
    layerAct = [[] for _ in range(3)]
    layerQuad = [[] for _ in range(3)]
    layerQuadSize = [[] for _ in range(3)]
    layerTriangle = [[] for _ in range(3)]
    eventChannels = [[] for _ in range(3)]

    end = layerOrder[0][0]
    middle = layerOrder[1][0]
    start = layerOrder[2][0]

    ndx = layerOrder[2][1]
    layer = layerOrder[2][2]
    layerNdx = 2
    numQuads = len(layers[ndx - 1]) - 2

    for i in range(3):
        yp = start
        zvalue = start

        if i == 1:
            yp = middle
            zvalue = middle
        if i == 2:
            yp = end
            zvalue = end

        if dataGeometry[ndx][1] == "Tree":
            up = False
            layerStart.append("Tree")
        else:
            up = True
            layerStart.append("Pyramid")

        if dataGeometry[ndx][2] == "REVERSED":
            reversed = True
        else:
            reversed = False

        posQuadSize = len(dataGeometry[ndx]) - 3
        quadSize = float(dataGeometry[ndx][posQuadSize])
        cellSize = quadSize * size / 2.0
        overallCellSize = cellSize
        quadGap = size - cellSize

        xpSize = ((numQuads * 2) * cellSize) + startPoint
        quadNo = 0
        xp = startPoint

        while xp < xpSize:
            if quadNo <= numQuads:
                for quadMember in range(2):
                    if quadMember == 0:
                        quadNo += 1

                    if whichLayer == 'X':
                        channel = calculateAnalysisQuad(
                            event, layer, up, xp, yp, channel, layerAct, reversed, numQuads,
                            xCoord, subtractPedX, layerQuad, quadNo, layerQuadSize,
                            cellSize, quadGap, layerTriangle, eventChannels
                        )
                    else:
                        channel = calculateAnalysisQuad(
                            event, layer, up, xp, yp, channel, layerAct, reversed, numQuads,
                            yCoord, subtractPedY, layerQuad, quadNo, layerQuadSize,
                            cellSize, quadGap, layerTriangle, eventChannels
                        )

                    xp += cellSize

            xp += quadGap

        channel = 0
        layerNdx -= 1
        if layerNdx >= 0:
            layer = layerOrder[layerNdx][2]
            ndx = layerOrder[layerNdx][1]

    calculateAnalysisTrack(
        whichLayer, event, layerAct, layerQuad, layerQuadSize, layerTriangle,
        layerOrder, eventChannels, layerStart, overallCellSize,
        x_ranges, y_ranges
    )
# end of calculateAnalysisLayer
