import math
import sys
import os
import re
from mplcursors import cursor
from dateutil import parser
from alive_progress import alive_bar
from collections import Counter
from itertools import groupby
from typing import Any, Dict, Tuple, List
from pathlib import Path

# helper: safely convert a list of values to a numpy float array, coercing non-numeric to np.nan
def to_float_array(lst):
    import numpy as _np
    if lst is None:
        return _np.array([], dtype=float)
    out = _np.empty(len(lst), dtype=float)
    for i, v in enumerate(lst):
        try:
            out[i] = float(v)
        except Exception:
            # try common dict-like access (some points stored as {'x': val} in some exports)
            try:
                if hasattr(v, 'get'):
                    cand = v.get('x', v.get('x3', None))
                    out[i] = float(cand)
                else:
                    out[i] = _np.nan
            except Exception:
                out[i] = _np.nan
    return out

def resource_path(relative_path: str) -> str:
    if getattr(sys, 'frozen', False):
        # PyInstaller bundles files into a temp folder accessible via _MEIPASS
        base_path = getattr(sys, '_MEIPASS', os.path.dirname(__file__))
    else:
        base_path = os.path.dirname(__file__)
    return os.path.join(base_path, relative_path)
#end of resource_path

# Optional runtime flags
export_tracking6_all = False

if len(sys.argv) > 1:
    # Expect the input file to already be prepared (six-hits or event file).
    input_file_name = sys.argv[1]
    print("Using input file:", input_file_name)
    run_info = re.findall(r'\d+', input_file_name)
    # optional channel range arguments remain supported (same semantics)
    x_ranges = [None, None, None]
    y_ranges = [None, None, None]
    for arg in sys.argv[2:]:
        mglobx = re.match(r'X=(\d+)-(\d+)', arg)
        mgloby = re.match(r'Y=(\d+)-(\d+)', arg)
        if mglobx:
            vmin = int(mglobx.group(1)); vmax = int(mglobx.group(2))
            x_ranges = [(vmin, vmax), (vmin, vmax), (vmin, vmax)]
        if mgloby:
            vmin = int(mgloby.group(1)); vmax = int(mgloby.group(2))
            y_ranges = [(vmin, vmax), (vmin, vmax), (vmin, vmax)]
        if arg == '--export-tracking6-all':
            export_tracking6_all = True
            print('Flag --export-tracking6-all detected; will export tracking6 CSV after analysis')
    for arg in sys.argv[2:]:
        mxi = re.match(r'X([0-2])=(\d+)-(\d+)', arg)
        myi = re.match(r'Y([0-2])=(\d+)-(\d+)', arg)
        if mxi:
            idx = int(mxi.group(1)); x_ranges[idx] = (int(mxi.group(2)), int(mxi.group(3)))
        if myi:
            idx = int(myi.group(1)); y_ranges[idx] = (int(myi.group(2)), int(myi.group(3)))
    def _range_str(r):
        return 'ALL' if r is None else f"{r[0]}-{r[1]}"
    runComments = f"Using channel ranges: X0={_range_str(x_ranges[0])} X1={_range_str(x_ranges[1])} X2={_range_str(x_ranges[2])} Y0={_range_str(y_ranges[0])} Y1={_range_str(y_ranges[1])} Y2={_range_str(y_ranges[2])} "
    print(f"Using channel ranges: X0={_range_str(x_ranges[0])} X1={_range_str(x_ranges[1])} X2={_range_str(x_ranges[2])} ")
    print(f"                       Y0={_range_str(y_ranges[0])} Y1={_range_str(y_ranges[1])} Y2={_range_str(y_ranges[2])} ")
    def _build_range_suffix(x_ranges, y_ranges):
        parts = []
        for i in range(3):
            parts.append(f"X{i}-" + (_range_str(x_ranges[i])))
        for i in range(3):
            parts.append(f"Y{i}-" + (_range_str(y_ranges[i])))
        return "_".join(parts)

    range_suffix = _build_range_suffix(x_ranges, y_ranges)
else:
    print("Usage: python analyze_pyramid_data.py <input_file> [X=..] [Y=..]")
    sys.exit(1)
    sys.exit(0)

# now start with data analysis
with alive_bar(len(subtractPedX)) as bar:
    for event in range(len(subtractPedX)):
        calculateAnalysisLayer('X', event, layerOrderX, x_ranges, y_ranges)
        calculateAnalysisLayer('Y', event, layerOrderY, x_ranges, y_ranges)
        bar.title("Analyzing data...")
        bar()

def populate(option, layer, length):
    xvals = [0 for x in range(length)]
    for y in range(len(xvals)):
        xvals[y] = y
    vals = [0 for x in range(length)]
    pedestal = []
    if option == 'x':
        pedestal = subtractPedX
    else:
        pedestal = subtractPedY
    for a in range(len(pedestal)):
        for b in range(length):
            if pedestal[a][layer][b] > 0:
                vals[b] += 1
    # print(option, layer, vals)
    return xvals, vals
# end of populate

def get6planemiddlehits(arr):
    xvals = []
    yvals = []
    #print(f"Total 6 plane middle hits: {len(arr)}")
    for i in range(len(arr)):
        # print(arr[i])
        xvals.append(arr[i][1][1][0])
        yvals.append(arr[i][1][4][0])
    # print (xvals,yvals)
    return xvals, yvals
# end of get6planemiddlehits

def get6planetophits(arr):
    xvals = []
    yvals = []
    #print(f"Total 6 plane top hits: {len(arr)}")
    for i in range(len(arr)):
        # print(arr[i])
        xvals.append(arr[i][1][0][0])
        yvals.append(arr[i][1][3][0])
    # print (xvals,yvals)
    return xvals, yvals
# end of get6planetophits

def get6planebottomhits(arr):
    xvals = []
    yvals = []
    #print(f"Total 6 plane bottom hits: {len(arr)}")
    for i in range(len(arr)):
        # print(arr[i])
        xvals.append(arr[i][1][2][0])
        yvals.append(arr[i][1][5][0])
    # print (xvals,yvals)
    return xvals, yvals
# end of get6planebottom    hits

def get6planemiddlehitsTimestamps(arr):
    xvals = []
    yvals = []
    ts = eventTime
    for i in range(len(arr)):
        eventIndex = arr[i][0]
        if ts[eventIndex]:
            timeVal = float(ts[eventIndex][0])
            xvals.append(eventIndex)
            yvals.append(timeVal)
    return yvals
# end of get6planemiddlehitsTimestamps

def get6planemiddlehitsTracksPerMinute(arr):
    xvals = []
    yvals = []
    startTime = 0
    minuteTime = microMinute + arr[0]
    trackCounter = 0
    for i in range(len(arr)):
        time = arr[i]
        if time <= minuteTime:
            trackCounter += 1
        else:
            xvals.append(startTime + 1)
            yvals.append(trackCounter)
            startTime += 1
            trackCounter = 0
            minuteTime = microMinute + arr[i]
    xvals.append(startTime)
    yvals.append(trackCounter)
    return xvals, yvals
# end of get6planemiddlehitsTracksPerMinute

def export_tracking6_middle_hit_entry(i, filename=None):
    """Export a single tracking6MiddleHitsXY[i] entry to CSV.
    The CSV will contain one row with columns:
    event, p0_x, p0_y, p1_x, p1_y, ..., expected_x, expected_y
    """
    if filename is None:
        filename = f"tracking6MiddleHitsXY_{i}.csv"
    if i < 0 or i >= len(tracking6MiddleHitsXY):
        raise IndexError(f"Index out of range: {i}")
    entry = tracking6MiddleHitsXY[i]
    event = entry[0]
    points = entry[1] if len(entry) > 1 else []
    expected_x = entry[2] if len(entry) > 2 else ''
    expected_y = entry[3] if len(entry) > 3 else ''
    # build header
    headers = ['event']
    for pndx in range(len(points)):
        headers.append(f'p{pndx}_x')
        headers.append(f'p{pndx}_y')
    headers += ['expected_x', 'expected_y']
    # build row
    row = [event]
    for p in points:
        try:
            row.append(p[0])
            row.append(p[1])
        except Exception:
            # non-standard point format: stringify
            row.append(str(p))
            row.append('')
    row += [expected_x, expected_y]
    # write csv
    try:
        import csv
        with open(filename, 'w', encoding='utf-8', newline='') as _csvf:
            writer = csv.writer(_csvf)
            writer.writerow(headers)
            writer.writerow(row)
        print(f'Wrote tracking6 entry CSV: {filename}')
    except Exception as _e:
        print(f'Failed to write tracking6 entry CSV: {_e}')

def export_tracking6_middle_hits_all(filename='tracking6MiddleHitsXY_all.csv'):
    """Export all entries in tracking6MiddleHitsXY to a single CSV.
    Each row corresponds to one entry; columns are event, p0_x,p0_y,...,expected_x,expected_y.
    The number of point columns is determined from the longest points list in the data.
    """
    # determine max number of points (0 when empty)
    if not tracking6MiddleHitsXY:
        max_points = 0
    else:
        max_points = max(len(e[1]) if len(e) > 1 and isinstance(e[1], list) else 0 for e in tracking6MiddleHitsXY)
    headers = ['event']
    for pndx in range(max_points):
        headers.append(f'p{pndx}_x')
        headers.append(f'p{pndx}_y')
    headers += ['expected_x', 'expected_y']
    try:
        import csv
        with open(filename, 'w', encoding='utf-8', newline='') as _csvf:
            writer = csv.writer(_csvf)
            writer.writerow(headers)
            for entry in tracking6MiddleHitsXY:
                event = entry[0]
                points = entry[1] if len(entry) > 1 else []
                expected_x = entry[2] if len(entry) > 2 else ''
                expected_y = entry[3] if len(entry) > 3 else ''
                row = [event]
                for p in points:
                    try:
                        row.append(p[0])
                        row.append(p[1])
                    except Exception:
                        row.append(str(p))
                        row.append('')
                # pad missing point columns
                missing_cols = (max_points - len(points)) * 2
                if missing_cols > 0:
                    row += [''] * missing_cols
                row += [expected_x, expected_y]
                writer.writerow(row)
        print(f'Wrote tracking6 all entries CSV: {filename}')
    except Exception as _e:
        print(f'Failed to write tracking6 all entries CSV: {_e}')

def get6singlepoints(option, arr):
    xvals = []
    yvals = []
    # print(option, len(arr))
    for i in range(len(arr)):
        xvals.append(arr[i][1][1][0])
        yvals.append(arr[i][1][4][0])
    return xvals, yvals
# end of get6singlepoints

def get6singlepointsBothLayers(option, arr1):
    xvals = []
    yvals = []
    # print(option,len(arr1))
    for i in range(len(arr1)):
        xvals.append(arr1[i][1][1][0])
        yvals.append(arr1[i][1][4][0])
    return xvals, yvals
# end of get6singlepintsBothLayers

def arrayMin(arr):
    min = 10000
    for i in range(len(arr)):
        if arr[i] < min:
            min = arr[i]
    return min
# end of arrayMin

def arrayMax(arr):
    max = -10000
    for i in range(len(arr)):
        if arr[i] > max:
            max = arr[i]
    return max
# end of arrayMax

def floatRange(start, stop, step):
    while start < stop:
        yield start
        start += step
# end of floatRange

def getBinnedData(arr, intervalSize):
    bins = []
    binCount = 0
    interval = intervalSize
    arrayMinValue = arrayMin(arr) - intervalSize
    arrayMaxValue = arrayMax(arr) + intervalSize
    for i in floatRange(arrayMinValue, arrayMaxValue, interval):
        bins.append(attrdict(binNum=i, minNum=i, maxNum=i + interval, count=0))
        binCount += 1

    totalCount = 0
    for i in range(len(arr)):
        item = arr[i]
        for j in range(len(bins)):
            bin = bins[j]
            if item > bin.minNum and item <= bin.maxNum:
                bin.count += 1
                totalCount += 1
    # print (intervalSize, arrayMinValue, arrayMaxValue)
    # for i in range(len(bins)):
    #	print(bins[i])
    return bins
# end of getBinnedData

def getFrequency6ExpectedActualforHitsSingleLayer(option, arr):
    diff = 0
    diffCollection = []
    xvals = []
    yvals = []
    if option == 'X':
        for i in range(len(arr)):
            diff = arr[i][2].x3 - arr[i][1][1][0]
            diffCollection.append(diff)
    if option == 'Y':
        for i in range(len(arr)):
            diff = arr[i][2].x3 - arr[i][1][4][0]
            diffCollection.append(diff)
    binnedData = getBinnedData(diffCollection, 0.2)
    for i in range(len(binnedData)):
        xvals.append(binnedData[i].binNum)
        yvals.append(binnedData[i].count)
    return xvals, yvals
# end of getFrequency6ExpectedActualforHitsSingleLayer

def getFrequency6ExpectedActualforHits(option, arr):
    diff = 0
    diffCollection = []
    xvals = []
    yvals = []
    # for i in range(len(arr)):
    #	for j in range(len(arr[i])):
    #		print (arr[i][j])
    if option == 'X':
        for i in range(len(arr)):
            # print(arr[i])
            diff = arr[i][2].x3 - arr[i][1][1][0]
            diffCollection.append(diff)
    if option == 'Y':
        for i in range(len(arr)):
            diff = arr[i][3].x3 - arr[i][1][4][0]
            diffCollection.append(diff)
    # print (diffCollection)
    binnedData = getBinnedData(diffCollection, 0.2)
    for i in range(len(binnedData)):
        xvals.append(binnedData[i].binNum)
        yvals.append(binnedData[i].count)
    return xvals, yvals
# end of getFrequency6ExpectedActualforHits

def getFrequency6ExpectedActual(option, arr1):
    xvals = []
    yvals = []
    diff = 0
    diffCollection = []
    if option == 'X':
        for i in range(len(arr1)):
            diff = arr1[i][2].x3 - arr1[i][1][1][0]
            diffCollection.append(diff)
    if option == 'Y':
        for i in range(len(arr1)):
            diff = arr1[i][2].x3 - arr1[i][1][4][0]
            diffCollection.append(diff)

    binnedData = getBinnedData(diffCollection, 1.0)
    for i in range(len(binnedData)):
        xvals.append(binnedData[i].binNum)
        yvals.append(binnedData[i].count)
    return xvals, yvals
# end of getFrequency6ExpectedActual

def getDeltaXYforhits(option, arr):
    xvals = []
    yvals = []
    events = []
    # print(arr)
    for i in range(len(arr)):
        if option == 'TB':
            deltax = arr[i][1][2][0] - arr[i][1][0][0]
            deltay = arr[i][1][5][0] - arr[i][1][3][0]
            xvals.append(deltax)
            yvals.append(deltay)
            events.append(arr[i][0])
    return xvals, yvals, events
# end of getDeltaXYforhits

def get6planemiddlemissed(arr, option):
    xvals = []
    yvals = []
    for i in range(len(arr)):
        if len(arr[i]) == 3:
            if option == 'X':
                xvals.append(arr[i][2].x3)
                yvals.append(arr[i][1][4][0])
            if option == 'Y':
                xvals.append(arr[i][1][1][0])
                yvals.append(arr[i][2].x3)
        if len(arr[i]) == 4:
            xvals.append(arr[i][2].x3)
            yvals.append(arr[i][3].x3)

    return xvals, yvals
# end of get6planemiddlemissed

def get5planemissing(arr, option):
    xvals = []
    yvals = []
    if option == 'TX':
        for i in range(len(arr)):
            xvals.append(arr[i][2].x3)
            yvals.append(arr[i][1][3][0])
    if option == 'MX':
        for i in range(len(arr)):
            xvals.append(arr[i][2].x3)
            yvals.append(arr[i][1][4][0])
    if option == 'BX':
        for i in range(len(arr)):
            xvals.append(arr[i][2].x3)
            yvals.append(arr[i][1][5][0])
    if option == 'TY':
        for i in range(len(arr)):
            xvals.append(arr[i][1][0][0])
            yvals.append(arr[i][2].x3)
    if option == 'MY':
        for i in range(len(arr)):
            xvals.append(arr[i][1][1][0])
            yvals.append(arr[i][2].x3)
    if option == 'BY':
        for i in range(len(arr)):
            xvals.append(arr[i][1][2][0])
            yvals.append(arr[i][2].x3)
    return xvals, yvals
# end of get5planemissing

def get4planemissing(arr, option):
    xvals = []
    yvals = []
    for i in range(len(arr)):
        xvals.append(arr[i][1].x3)
        yvals.append(arr[i][2].x3)
    return xvals, yvals
# end of get4planemissing

dxbothlayers = []
dybothlayers = []
dxtopmiddlebothlayers = []
dytopmiddlebothlayers = []
dxbottommiddlebothlayers = []
dybottommiddlebothlayers = []

def getAnalysisBothLayers():
    global dx
    global dy
    global dxbothlayers
    global dybothlayers
    # reset combined lists to avoid duplicates if this is called more than once
    dxbothlayers = []
    dybothlayers = []
    for i in range(len(dx)):
        event = dx[i][0]
        for j in range(len(dy)):
            if dy[j][0] == event:
                dxbothlayers.append(dx[i])
                dybothlayers.append(dy[j])
# end of getAnalysisBothLayers

def getAnalysisTopMiddleBothLayers():
    global dxtopmiddle
    global dytopmiddle
    global dxtopmiddlebothlayers
    global dytopmiddlebothlayers
    # reset combined lists to avoid duplicates if this is called more than once
    dxtopmiddlebothlayers = []
    dytopmiddlebothlayers = []
    for i in range(len(dxtopmiddle)):
        event = dxtopmiddle[i][0]
        for j in range(len(dytopmiddle)):
            if dytopmiddle[j][0] == event:
                dxtopmiddlebothlayers.append(dxtopmiddle[i])
                dytopmiddlebothlayers.append(dytopmiddle[j])
# end of getAnalysisTopMiddleBothLayers

def getAnalysisBottomMiddleBothLayers():
    global dxbottommiddle
    global dybottommiddle
    global dxbottommiddlebothlayers
    global dybottommiddlebothlayers
    # reset combined lists to avoid duplicates if this is called more than once
    dxbottommiddlebothlayers = []
    dybottommiddlebothlayers = []
    for i in range(len(dxbottommiddle)):
        event = dxbottommiddle[i][0]
        for j in range(len(dybottommiddle)):
            if dybottommiddle[j][0] == event:
                dxbottommiddlebothlayers.append(dxbottommiddle[i])
                dybottommiddlebothlayers.append(dybottommiddle[j])
# end of getAnalysisMiddleBottomBothLayers

getAnalysisBothLayers()
getAnalysisTopMiddleBothLayers()
getAnalysisBottomMiddleBothLayers()

# Diagnostics: detect any entries where an event id is empty or missing
def _diagnose_empty_event_ids():
    lists_to_check = {
        'dxbothlayers': dxbothlayers,
        'dybothlayers': dybothlayers,
        'dxtopmiddlebothlayers': dxtopmiddlebothlayers,
        'dxbottommiddlebothlayers': dxbottommiddlebothlayers,
        'tracking6MiddleHitsXY': tracking6MiddleHitsXY,
    }
    for name, lst in lists_to_check.items():
        missing = []
        for i, item in enumerate(lst):
            try:
                ev = item[0]
            except Exception:
                ev = None
            if ev is None or (isinstance(ev, str) and ev.strip() == ''):
                missing.append((i, item))
        if missing:
            print(f"Diagnostic: {len(missing)} empty event ids found in {name}; sample:")
            for idx, it in missing[:10]:
                print(f"  {name}[{idx}] = {it}")

# Run diagnostics now so the console shows any empty event ids early
_diagnose_empty_event_ids()
def _check_histogram_consistency(H, bin_events, xedges, yedges, name, xs=None, ys=None, events=None):
    """
    Compare counts in H against collected per-bin lists in bin_events.
    If a mismatch is found, print diagnostic details and, when available,
    list the point indices/representations that fall into the bin according
    to the histogram edges (using the provided xs, ys, events arrays).
    """
    try:
        import numpy as _np
    except Exception:
        _np = None
    nbx = len(xedges) - 1
    nby = len(yedges) - 1
    mismatches = 0
    for xi in range(nbx):
        for yi in range(nby):
            try:
                cnt = int(H[xi, yi])
            except Exception:
                try:
                    cnt = int(H[xi][yi])
                except Exception:
                    cnt = 0
            collected_len = len(bin_events[xi][yi]) if bin_events and xi < len(bin_events) and yi < len(bin_events[0]) else 0
            if cnt != collected_len:
                mismatches += 1
                #print(f"CONSISTENCY MISMATCH in {name}: bin ({xi},{yi}) cnt={cnt} but collected_len={collected_len}")
                try:
                    sample = bin_events[xi][yi][:10]
                    #print(f"  collected sample (first 10): {repr(sample)}")
                except Exception:
                    pass
                # If raw points available, show which points fall into this bin using edges
                if _np is not None and xs is not None and ys is not None and events is not None:
                    try:
                        dx = _np.array(xs)
                        dy = _np.array(ys)
                        if xi == nbx - 1:
                            xmask = (dx >= xedges[xi]) & (dx <= xedges[xi + 1])
                        else:
                            xmask = (dx >= xedges[xi]) & (dx < xedges[xi + 1])
                        if yi == nby - 1:
                            ymask = (dy >= yedges[yi]) & (dy <= yedges[yi + 1])
                        else:
                            ymask = (dy >= yedges[yi]) & (dy < yedges[yi + 1])
                        mask = xmask & ymask
                        indices = [k for k, m in enumerate(mask) if m]
                        #print(f"  points falling into bin according to edges: count={len(indices)}; indices sample={indices[:20]}")
                        #for k in indices[:20]:
                        #    try:
                        #        print(f"    idx={k} x={xs[k]} y={ys[k]} ev_repr={repr(events[k])}")
                        #    except Exception:
                        #        pass
                    except Exception as _e:
                        print(f"  Failed to compute edge-based membership for bin ({xi},{yi}): {_e}")
    #if mismatches:
    #    print(f"CONSISTENCY: {mismatches} mismatched bins in {name}")
#end of check consistency

def write_2d_histogram_event_csv(H, xedges, yedges, x_values, y_values, events, report_stem, csv_stem, check_consistency_func=_check_histogram_consistency):
    """Write a CSV with per-bin event ids for a 2D histogram.
    Parameters:
    - H, xedges, yedges: histogram arrays returned by matplotlib.hist2d
    - x_values, y_values: raw x/y arrays used to build the histogram
    - events: list of event ids (parallel to x_values/y_values)
    - report_stem: prefix for output filenames
    - csv_stem: suffix for this histogram (no '.csv')
    - check_consistency_func: function to call to validate histogram (optional)
    """
    nbx = len(xedges) - 1
    nby = len(yedges) - 1
    bin_events = [[[] for _ in range(nby)] for _ in range(nbx)]
    try:
        import numpy as _np
        x_idx = _np.digitize(_np.array(x_values), xedges) - 1
        y_idx = _np.digitize(_np.array(y_values), yedges) - 1
        for idx, ev in enumerate(events):
            xi = int(x_idx[idx])
            yi = int(y_idx[idx])
            if xi < 0 or yi < 0 or xi >= nbx or yi >= nby:
                continue
            bin_events[xi][yi].append(ev)
    except Exception:
        # fallback: leave bin_events empty and rely on later logic
        pass

    try:
        if check_consistency_func is not None:
            check_consistency_func(H, bin_events, xedges, yedges, f"{report_stem}_{csv_stem}", x_values, y_values, events)
    except Exception:
        pass

    out_csv = f"{report_stem}_{csv_stem}.csv"
    missing_count = 0
    try:
        with open(out_csv, 'w', encoding='utf-8') as _hf:
            _hf.write('# x_bin_index,y_bin_index,x_center,y_center,count,event_ids\n')
            for xi in range(nbx):
                x_center = (xedges[xi] + xedges[xi + 1]) / 2.0
                for yi in range(nby):
                    y_center = (yedges[yi] + yedges[yi + 1]) / 2.0
                    try:
                        cnt = int(H[xi, yi])
                    except Exception:
                        cnt = int(H[xi][yi])
                    if cnt > 0:
                        try:
                            import numpy as _np
                            dx = _np.array(x_values)
                            dy = _np.array(y_values)
                            if xi == nbx - 1:
                                xmask = (dx >= xedges[xi]) & (dx <= xedges[xi + 1])
                            else:
                                xmask = (dx >= xedges[xi]) & (dx < xedges[xi + 1])
                            if yi == nby - 1:
                                ymask = (dy >= yedges[yi]) & (dy <= yedges[yi + 1])
                            else:
                                ymask = (dy >= yedges[yi]) & (dy < yedges[yi + 1])
                            mask = xmask & ymask
                            evs_in_bin = [events[k] for k, m in enumerate(mask) if m]
                        except Exception:
                            evs_in_bin = bin_events[xi][yi]
                        evs_filtered = [str(e) for e in evs_in_bin if e is not None and str(e).strip() != '']
                        if not evs_filtered:
                            evs_str = 'MISSING'
                            missing_count += 1
                        else:
                            evs_str = ';'.join(evs_filtered)
                        _hf.write(f"{xi},{yi},{x_center},{y_center},{cnt},\"{evs_str}\"\n")
        print(f"Wrote 2D histogram data: {out_csv}")
        if missing_count:
            print(f"Warning: {missing_count} bins had count>0 but no non-empty event ids in {out_csv}")
    except Exception as _e:
        print(f"Failed to write 2D histogram data for {csv_stem}: {_e}")
#end of write_2d_histogram_event_csv

def getFrequency(arr1):
    xvals = []
    yvals = []
    c = Counter(arr1)
    xvals = c.keys()
    yvals = c.values()
    return xvals, yvals
# end of getFrequency

def getChannelData(whichLayer, arr1, upperLimit):
    vals = []
    layerNdx = 0
    if whichLayer == 'top':
        layerNdx = 3
    if whichLayer == 'middle':
        layerNdx = 2
    if whichLayer == 'bottom':
        layerNdx = 1
    for i in range(len(arr1)):
        chan1 = arr1[i][layerNdx].channel1
        chan2 = arr1[i][layerNdx].channel2
        if chan1 != -1:
            if chan1 > upperLimit:
                vals.append(upperLimit)
            else:
                vals.append(chan1)
        if chan2 != -1:
            if chan2 > upperLimit:
                vals.append(upperLimit)
            else:
                vals.append(chan2)

    return vals
# end of getChannelData

def calculateDeltaXDeltaYFrequency(arr, binWidth):
    deltaValues = []
    for i in range(len(arr)):
        deltaValues.append(arr[i][4])
    deltaValues = sorted(deltaValues)
    minVal = arrayMin(deltaValues)
    maxVal = arrayMax(deltaValues)
    binBoundaries = []

    for i in floatRange(minVal, maxVal + binWidth, binWidth):
        binBoundaries.append(i)

    bins = [0 for x in range(len(binBoundaries) - 1)]
    for i in range(len(deltaValues)):
        value = deltaValues[i]
        for j in range(len(bins)):
            if value >= binBoundaries[j] and value < binBoundaries[j + 1]:
                bins[j] += 1
    xvals = []
    yvals = []
    for i in range(len(bins)):
        binCenter = (binBoundaries[i] + binBoundaries[i + 1]) / 2.0
        xvals.append(binCenter)
        yvals.append(bins[i])
    return xvals, yvals
# end of calculateDeltaXDeltaYFrequency

def getDxDy():
    xvals = []
    yvals = []
    events = []
    totalEvents = len(dxbothlayers)
    for i in range(totalEvents):
        xvals.append(dxbothlayers[i][4])
        yvals.append(dybothlayers[i][4])
        events.append(dxbothlayers[i][0])
    return xvals, yvals, events
# end of getDxDy

def getDxDyMiddle(arrX, arrY):
    xvals = []
    yvals = []
    events = []
    # totalEvents = len(arrX)
    for i in range(len(arrX)):
        xvals.append(arrX[i][4])
        yvals.append(arrY[i][4])
        events.append(arrX[0][1])
    return xvals, yvals, events
# end of getDxDyMiddle

def getDxDz():
    xvals = []
    yvals = []
    events = []
    events6hits = []
    for i in range(len(tracking6MiddleHitsXY)):
        events6hits.append(tracking6MiddleHitsXY[i][0])
    for i in range(len(dxbothlayers)):
        if dxbothlayers[i][5] != 0 and dybothlayers[i][5] != 0 and dxbothlayers[i][0] in events6hits:
            xvals.append(dxbothlayers[i][4] / dxbothlayers[i][5])
            yvals.append(dybothlayers[i][4] / dybothlayers[i][5])
            events.append(dxbothlayers[i][0])
    return xvals, yvals, events
# end of getDxDz

def getDxyDzMiddle(arrX, arrY):
    xvals = []
    yvals = []
    events = []
    for i in range(len(arrX)):
        if arrX[i][5] != 0 and arrY[i][5] != 0:
            xvals.append(arrX[i][4] / arrX[i][5])
            yvals.append(arrY[i][4] / arrY[i][5])
            events.append(arrX[i][0])
    return xvals, yvals, events
# end of getDxyDzMiddle

def getDxDzDyDzFor6HitsLEGO(option, deltaz):
    xvals = []
    yvals = []
    events = []
    totalEvents = len(dxbothlayers)
    events6planehits = []
    for i in range(len(tracking6MiddleHitsXY)):
        events6planehits.append(tracking6MiddleHitsXY[i][0])
    for i in range(len(dxbothlayers)):
        if option == 'TB':
            if dxbothlayers[i][0] in events6planehits:
                deltaxz = dxbothlayers[i][4] / dxbothlayers[i][5]
                deltayz = dybothlayers[i][4] / dybothlayers[i][5]
                xvals.append(deltaxz)
                yvals.append(deltayz)
                events.append(dxbothlayers[i][0])
        if option == 'TM':
            if dxbothlayers[i][0] in events6planehits:
                deltaxz = dxbothlayers[i][6] / dxbothlayers[i][7]
                deltayz = dybothlayers[i][6] / dybothlayers[i][7]
                xvals.append(deltaxz)
                yvals.append(deltayz)
                events.append(dxbothlayers[i][0])
    return xvals, yvals, events
# end of getDxDzDyDzFor6HitsLEGO


def compute_value_distributions(values, bins_x=50, bins_z=50,
                                range_x=None, range_z=None, density=False):
    """Compute distribution for the ratio X/Z from the provided `values` sequence.

    The function keeps the same signature for backward compatibility but instead
    of producing separate histograms for X and Z it computes the distribution
    of the ratio (X / Z) where X is taken from values[i][4] and Z from values[i][5].

    Parameters
    - values: sequence where each item is expected to be an indexable container
      and values[i][4] (deltax) and values[i][5] (deltaz) are numeric.
    - bins_x: number of bins or bin edges for the ratio histogram (used as primary).
    - bins_z, range_z: accepted for API compatibility but ignored (ratio uses bins_x/range_x).
    - range_x: optional (min,max) range to force for the ratio histogram.
    - density: if True return densities instead of raw counts.

    Returns (hist_ratio, edges_ratio, [], []) — the last two placeholders preserve
    the original 4-tuple return shape so existing callers keep working.
    """
    ratios = []
    for i in range(len(values)):
        try:
            x = values[i][4]
            z = values[i][5]
        except Exception:
            # unexpected format; skip this entry
            continue
        try:
            if z is None:
                continue
            # guard against zero division
            if float(z) == 0.0:
                continue
            ratio = float(x) / float(z)
            if math.isfinite(ratio):
                ratios.append(ratio)
        except Exception:
            continue

    if len(ratios) == 0:
        return [], [], [], []

    # Prefer numpy if available for histogramming
    try:
        import numpy as _np
        hist_ratio, edges_ratio = _np.histogram(_np.asarray(ratios), bins=bins_x, range=range_x, density=density)
        return hist_ratio.tolist(), edges_ratio.tolist(), [], []
    except Exception:
        # pure-Python fallback histogram for the single ratio array
        def _hist_manual(vals, bins, vrange):
            if hasattr(bins, '__iter__'):
                edges = list(bins)
            else:
                mn = vrange[0] if vrange is not None else min(vals)
                mx = vrange[1] if vrange is not None else max(vals)
                if mx == mn:
                    mx = mn + 1.0
                step = (mx - mn) / float(bins)
                edges = [mn + i * step for i in range(bins + 1)]
            counts = [0] * (len(edges) - 1)
            for v in vals:
                if v < edges[0] or v > edges[-1]:
                    continue
                for bi in range(len(edges) - 1):
                    left = edges[bi]
                    right = edges[bi + 1]
                    if (v >= left and v < right) or (bi == len(edges) - 2 and v == right):
                        counts[bi] += 1
                        break
            if density:
                total = float(sum(counts)) if sum(counts) > 0 else 1.0
                counts = [c / total / (edges[i + 1] - edges[i]) for i, c in enumerate(counts)]
            return counts, edges

        hist_ratio, edges_ratio = _hist_manual(ratios, bins_x, range_x)
        return hist_ratio, edges_ratio, [], []

def getDxDzDyDzFor6HitsLEGOATAN(option, deltaz):
    xvals = []
    yvals = []
    events = []
    global dxbothlayers
    global dybothlayers
    global tracking6MiddleHitsXY
    totalEvents = len(dxbothlayers)
    events6planehits = []
    for i in range(len(tracking6MiddleHitsXY)):
        events6planehits.append(tracking6MiddleHitsXY[i][0])
    for i in range(len(dxbothlayers)):
        if option == 'TB':
            if dxbothlayers[i][0] in events6planehits:
                atanx = math.atan2(dxbothlayers[i][5], dxbothlayers[i][4])
                atany = math.atan2(dybothlayers[i][5], dybothlayers[i][4])
                # Map to -90..90 degrees (principal arctan range)
                xdegree = math.degrees(atanx)
                #if xdegree > 90:
                #    xdegree -= 180
                #elif xdegree <= -90:
                #    xdegree += 180
                ydegree = math.degrees(atany)
                #if ydegree > 90:
                #    ydegree -= 180
                #elif ydegree <= -90:
                #    ydegree += 180
                xvals.append(xdegree)
                yvals.append(ydegree)
                events.append(dxbothlayers[i][0])
    return xvals, yvals, events
#end of getDxDzDyDzFor6HitsLEGOATAN

def getDxDzDyDzFor6HitsLEGOATAN2(option, deltaz):
    xvals = []
    yvals = []
    events = []
    global dxbothlayers
    global dybothlayers
    global tracking6MiddleHitsXY
    totalEvents = len(dxbothlayers)
    events6planehits = []
    for i in range(len(tracking6MiddleHitsXY)):
        events6planehits.append(tracking6MiddleHitsXY[i][0])
    for i in range(len(dxbothlayers)):
        if option == 'TB':
            if dxbothlayers[i][0] in events6planehits:
                atanx = math.atan2(dxbothlayers[i][5], dxbothlayers[i][4])
                atany = math.atan2(dybothlayers[i][5], dybothlayers[i][4])
                xdegree = math.degrees(atanx)
                #if xdegree > 90:
                #    xdegree -= 180
                #elif xdegree <= -90:
                #    xdegree += 180
                ydegree = math.degrees(atany)
                #if ydegree > 90:
                #    ydegree -= 180
                #elif ydegree <= -90:
                #    ydegree += 180
                xvals.append(xdegree)
                yvals.append(ydegree)
                events.append(dxbothlayers[i][0])
    return xvals, yvals, events
#end of getDxDzDyDzFor6HitsLEGOATAN2


def getDxDzDyDz4PlaneTracking(option, deltaz):
    xvals = []
    yvals = []
    events = []
    if option == 'MB':
        for i in range(len(dxbottommiddlebothlayers)):
            deltax = dxbottommiddlebothlayers[i][4] / dxbottommiddlebothlayers[i][5]
            deltay = dybottommiddlebothlayers[i][4] / dybottommiddlebothlayers[i][5]
            xvals.append(deltax)
            yvals.append(deltay)
            events.append(dxbottommiddlebothlayers[i][0])
    if option == 'TM':
        for i in range(len(dxtopmiddlebothlayers)):
            deltax = dxtopmiddlebothlayers[i][4] / dxtopmiddlebothlayers[i][5]
            deltay = dytopmiddlebothlayers[i][4] / dytopmiddlebothlayers[i][5]
            xvals.append(deltax)
            yvals.append(deltay)
            events.append(dxtopmiddlebothlayers[i][0])
    if option == 'TB':
        eventNums = []
        for i in range(len(tracking4MiddleMissing)):
            eventNums.append(tracking4MiddleMissing[i][0])
        for i in range(len(dxbothlayers)):
            if dxbothlayers[i][0] in eventNums:
                deltax = dxbothlayers[i][4] / dxbothlayers[i][5]
                deltay = dybothlayers[i][4] / dybothlayers[i][5]
                xvals.append(deltax)
                yvals.append(deltay)
                events.append(dxbothlayers[i][0])
    return xvals, yvals, events
#end of getDxDzDyDz4PlaneTracking

def getDxDzDyDz4PlaneTrackingATAN(option, deltaz):
    xvals = []
    yvals = []
    events = []
    global dxbottommiddlebothlayers
    global dybottommiddlebothlayers
    global dxtopmiddlebothlayers
    global dytopmiddlebothlayers
    global dxbothlayers
    global dybothlayers
    if option == 'MB':
        for i in range(len(dxbottommiddlebothlayers)):
            atanx = math.atan2(dxbottommiddlebothlayers[i][5], dxbottommiddlebothlayers[i][4])
            atany = math.atan2(dybottommiddlebothlayers[i][5], dybottommiddlebothlayers[i][4])
            xdegree = math.degrees(atanx)
            #if xdegree > 90:
            #    xdegree -= 180
            #elif xdegree <= -90:
            #    xdegree += 180
            ydegree = math.degrees(atany)
            #if ydegree > 90:
            #    ydegree -= 180
            #elif ydegree <= -90:
            #    ydegree += 180
            xvals.append(xdegree)
            yvals.append(ydegree)
            events.append(dxbottommiddlebothlayers[i][0])
    if option == 'TM':
        for i in range(len(dxtopmiddlebothlayers)):
            atanx = math.atan2(dxtopmiddlebothlayers[i][5], dxtopmiddlebothlayers[i][4])
            atany = math.atan2(dytopmiddlebothlayers[i][5], dytopmiddlebothlayers[i][4])
            xdegree = math.degrees(atanx)
            #if xdegree > 90:
            #    xdegree -= 180
            #elif xdegree <= -90:
            #    xdegree += 180
            ydegree = math.degrees(atany)
            #if ydegree > 90:
            #    ydegree -= 180
            #elif ydegree <= -90:
            #    ydegree += 180
            xvals.append(xdegree)
            yvals.append(ydegree)
            events.append(dxtopmiddlebothlayers[i][0])
    if option == 'TB':
        eventNums = []
        for i in range(len(tracking4MiddleMissing)):
            eventNums.append(tracking4MiddleMissing[i][0])
        for i in range(len(dxbothlayers)):
            if dxbothlayers[i][0] in eventNums:
                atanx = math.atan2(dxbothlayers[i][5], dxbothlayers[i][4])
                atany = math.atan2(dybothlayers[i][5], dybothlayers[i][4])
                xdegree = math.degrees(atanx)
                #if xdegree > 90:
                #    xdegree -= 180
                #elif xdegree <= -90:
                #    xdegree += 180
                ydegree = math.degrees(atany)
                #if ydegree > 90:
                #    ydegree -= 180
                #elif ydegree <= -90:
                #    ydegree += 180
                xvals.append(xdegree)
                yvals.append(ydegree)
                events.append(dxbothlayers[i][0])
    return xvals, yvals, events
#end of getDxDzDyDz4PlaneTrackingATAN

def getDeltaT(index1, index2):
    xvals = []
    yvals = []
    for i in range(len(eventTime)):
        time1 = eventTime[i][index1]
        time2 = eventTime[i][index2]
        if (time1 > 0 and time2 > 0):
            xvals.append(i)
            yvals.append(time2 - time1)

    return xvals, yvals
# end of getDeltaT

def getEventsWithTracksPerMinute(layerCount, option):
    xvals = []
    yvals = []
    xtop = layerOrderX[2][2] * 2
    xmiddle = layerOrderX[1][2] * 2
    xbottom = layerOrderX[0][2] * 2
    ytop = (layerOrderY[2][2] * 2) + 1
    ymiddle = (layerOrderY[1][2] * 2) + 1
    ybottom = (layerOrderY[0][2] * 2) + 1
    startTime = 0
    minuteTime = microMinute + eventTime[0][0]
    track_counter = 0
    for i in range(len(eventTime)):
        if layerCount == 4:
            if option == 'TM':
                if (eventTime[i][xtop] > 0 and
                        eventTime[i][xmiddle] > 0 and
                        eventTime[i][xbottom] <= 0 and
                        eventTime[i][ytop] > 0 and
                        eventTime[i][ymiddle] > 0 and
                        eventTime[i][ybottom] <= 0):
                    # check if it belongs within each minute
                    if (eventTime[i][0] <= minuteTime):
                        track_counter += 1
                    else:
                        # save and move up a minute
                        xvals.append(startTime + 1)
                        yvals.append(track_counter)
                        startTime += 1
                        track_counter = 0
                        minuteTime = microMinute + eventTime[i][0]
            else:
                # it is MB
                if (eventTime[i][xtop] <= 0 and
                        eventTime[i][xmiddle] > 0 and
                        eventTime[i][xbottom] > 0 and
                        eventTime[i][ytop] <= 0 and
                        eventTime[i][ymiddle] > 0 and
                        eventTime[i][ybottom] > 0):
                    # check if it belongs within each minute
                    if (eventTime[i][0] <= minuteTime):
                        track_counter += 1
                    else:
                        # save and move up a minute
                        xvals.append(startTime + 1)
                        yvals.append(track_counter)
                        startTime += 1
                        track_counter = 0
                        minuteTime = microMinute + eventTime[i][0]
        if layerCount == 5:
            if option == 'M':
                if ((eventTime[i][xtop] > 0 and
                     eventTime[i][xbottom] > 0 and
                     eventTime[i][ytop] > 0 and
                     eventTime[i][ybottom] > 0) and
                        ((eventTime[i][xmiddle] > 0 and eventTime[i][ymiddle] <= 0)
                         or (eventTime[i][xmiddle] <= 0 and eventTime[i][ymiddle] > 0))):
                    # check if it belongs within each minute
                    count = 0
                    for j in range(len(eventTime[i])):
                        if eventTime[i][j] > 0:
                            count += 1
                    if (eventTime[i][0] <= minuteTime and count == layerCount):
                        track_counter += 1
                    else:
                        # save and move up a minute
                        xvals.append(startTime + 1)
                        yvals.append(track_counter)
                        startTime += 1
                        track_counter = 0
                        minuteTime = microMinute + eventTime[i][0]
            else:
                # it is TB, either top or bottom missing
                count = 0
                for j in range(len(eventTime[i])):
                    if eventTime[i][j] > 0:
                        count += 1
                if (eventTime[i][xmiddle] > 0 and eventTime[i][ymiddle] > 0 and count == layerCount):
                    if (eventTime[i][0] <= minuteTime):
                        track_counter += 1
                    else:
                        # save and move up a minute
                        xvals.append(startTime + 1)
                        yvals.append(track_counter)
                        startTime += 1
                        track_counter = 0
                        minuteTime = microMinute + eventTime[i][0]
        if layerCount == 6:
            if (eventTime[i][xtop] > 0 and
                    eventTime[i][xmiddle] > 0 and
                    eventTime[i][xbottom] > 0 and
                    eventTime[i][ytop] > 0 and
                    eventTime[i][ymiddle] > 0 and
                    eventTime[i][ybottom] > 0):
                # check if it belongs within each minute
                if (eventTime[i][0] <= minuteTime):
                    track_counter += 1
                else:
                    # save and move up a minute
                    xvals.append(startTime + 1)
                    yvals.append(track_counter)
                    # print(layerCount, xvals, yvals)
                    startTime += 1
                    track_counter = 0
                    minuteTime = microMinute + eventTime[i][0]
    xvals.append(startTime + 1)
    yvals.append(track_counter)
    return xvals, yvals
# end of getEventsWithTracksPerMinute

def popADR(option, layer, length):
    vals = []
    pedestal = []
    if option == 'x':
        pedestal = subtractPedX
    else:
        pedestal = subtractPedY
    for event in range(len(pedestal)):
        for channel in range(1, len(pedestal[event][layer])):
            if pedestal[event][layer][channel - 1] > 0 and pedestal[event][layer][channel] > 0:
                xcoord = channel - 1
                ycoord = pedestal[event][layer][channel - 1] + pedestal[event][layer][channel]
                line = attrdict(x=xcoord, y=ycoord)
                vals.append(line)
    x = []
    for i in range(len(vals)):
        x.append(vals[i].x)
    y = []
    for i in range(len(vals)):
        y.append(vals[i].y)
    # print(option, layer, vals)
    # for i in range(len(y)):
    #	print(y[i])
    return x, y
# end of popXADR

def getAverage(data, length):
    x = [0 for i in range(length)]
    for y in range(len(x)):
        x[y] = y
    out_y = [0 for i in range(length)]
    for i in range(len(x)):
        s = 0
        cnt = 0
        for j in range(len(data)):
            if i == data[j].x:
                s += data[j].y
                cnt += 1
        if cnt > 0:
            out_y[i] = s / cnt  # type: ignore
    return x, out_y
#end of getAverage

def popADRAverage(option, layer, length):
    vals = []
    pedestal = []
    if option == 'x':
        pedestal = subtractPedX
    else:
        pedestal = subtractPedY
    for event in range(len(pedestal)):
        for channel in range(1, len(pedestal[event][layer])):
            if pedestal[event][layer][channel - 1] > 0 and pedestal[event][layer][channel] > 0:
                xcoord = channel - 1
                ycoord = pedestal[event][layer][channel - 1] + pedestal[event][layer][channel]
                line = attrdict(x=xcoord, y=ycoord)
                vals.append(line)
    x, y = getAverage(vals, length)
    # print(option, layer)
    # for i in range(len(y)):
    #	print(y[i])
    return x, y
# end of popADRAverage

