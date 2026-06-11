import re
import sys
import math
import matplotlib.pyplot as plt
plt.rcParams['figure.max_open_warning'] = 0
import numpy as np
import matplotlib.backends.backend_pdf
from mplcursors import cursor
from dateutil import parser
from alive_progress import alive_bar
from collections import Counter
from itertools import groupby
from typing import Any, Dict, Tuple, List
from pathlib import Path
import os

xLayerLength = (len(layers[4]) - 2) * 4
yLayerLength = (len(layers[5]) - 2) * 4

xLabels = []
for i in range(0, xLayerLength):
    xLabels.append('Channel ' + str(i + 1))
yLabels = []
for i in range(0, yLayerLength):
    yLabels.append('Channel ' + str(i + 1))


deltaxzyz_figures = []

def customize6PlaneHitsPlot(ax, fs, anchorx, anchory):
    cursor(hover=True)
    ax.grid(zorder=-1.0)
    ax.legend(loc='upper center', bbox_to_anchor=[anchorx, anchory], ncol=1, fontsize=fs)

# before plotting the 6-plane middle-hits, write a small report summarizing how many
# best six-hit tracks were found (after any channel-range filtering applied).
from pathlib import Path as _Path
report_stem = _Path(input_file_name).stem
# append the compact range suffix so reports and CSVs carry range info
try:
    if range_suffix:
        report_stem = f"{report_stem}_{range_suffix}"
except NameError:
    # range_suffix not defined (shouldn't happen) — leave report_stem unchanged
    pass
report_filename = f"{report_stem}_6hits_report.txt"
try:
    with open(report_filename, 'w', encoding='utf-8') as _rf:
        from datetime import datetime as _dt
        _rf.write(f"Report generated: {_dt.now().isoformat()}\n")
        _rf.write(f"Input file: {input_file_name}\n")
        # channel range info (per-board)
        def _rstr(r):
            return 'ALL' if not r else f"{r[0]}-{r[1]}"
        _rf.write(f"X0: {_rstr(x_ranges[0])} X1: {_rstr(x_ranges[1])} X2: {_rstr(x_ranges[2])}\n")
        _rf.write(f"Y0: {_rstr(y_ranges[0])} Y1: {_rstr(y_ranges[1])} Y2: {_rstr(y_ranges[2])}\n")
        _rf.write(f"Total best 6-hit tracks (tracking6MiddleHitsXY): {len(tracking6MiddleHitsXY)}\n")
        _rf.write("Event IDs for best 6-hit tracks:\n")
        for _item in tracking6MiddleHitsXY:
            try:
                _rf.write(str(_item[0]) + "\n")
            except Exception:
                # defensive: if structure unexpected, dump repr
                _rf.write(repr(_item) + "\n")
    print(f"Wrote 6-hit report: {report_filename}")
except Exception as _e:
    print(f"Failed to write 6-hit report: {_e}")

# Write a combined per-point report listing each channel pair and whether it was ACCEPTED or REMOVED
try:
    report_combined = f"{report_stem}_points_by_range_status.txt"
    with open(report_combined, 'w', encoding='utf-8') as _rf4:
        from datetime import datetime as _dt
        _rf4.write(f"Combined accepted/removed by channel range report: {_dt.now().isoformat()}\n")
        _rf4.write(f"Input file: {input_file_name}\n")
        _rf4.write("# event,layer,board,plane_pos,channel1,channel2,status\n")
        records = {}
        # collect removed entries
        for rec in filtered_out_by_range:
            try:
                key = (rec.get('event'), rec.get('layer'), rec.get('board'), rec.get('plane_pos'))
                removed = rec.get('removed', [])
                for (c1, c2) in removed:
                    records.setdefault(key, []).append((c1, c2, 'REMOVED'))
            except Exception:
                # skip malformed
                continue
        # collect accepted entries
        for rec in accepted_by_range:
            try:
                key = (rec.get('event'), rec.get('layer'), rec.get('board'), rec.get('plane_pos'))
                accepted = rec.get('accepted', [])
                for (c1, c2) in accepted:
                    records.setdefault(key, []).append((c1, c2, 'ACCEPTED'))
            except Exception:
                continue

        # write out sorted by event->layer->board->plane
        for key in sorted(records.keys()):
            evt, layer, board, plane = key
            for (c1, c2, status) in records[key]:
                _rf4.write(f"{evt},{layer},{board},{plane},{c1},{c2},{status}\n")
    print(f"Wrote combined points-by-range-status report: {report_combined}")
except Exception as _e:
    print(f"Failed to write combined points-by-range-status report: {_e}")

figGa, axGa = plt.subplots(1, 1, figsize=(15, 8))
hit6middleX, hit6middleY = get6planemiddlehits(tracking6MiddleHitsXY)
#for i in range(len(hit6middleX)):
#    print(hit6middleX[i], hit6middleY[i])
axGa.scatter(hit6middleX, hit6middleY, facecolor="magenta", s=16, linewidth=0.3, edgecolor='none', zorder=3, alpha=0.9,
            label='6 PLANE TRACKING - MIDDLE POINTS IN XY ' + runComments)
# Keep the Y scale fixed starting at 0 up to yLayerLength*pointWidth as requested.
axGa.set_xlim(0, (xLayerLength * pointWidth))
axGa.set_ylim(0, (yLayerLength * pointWidth))
customize6PlaneHitsPlot(axGa, 10, 0.5, 1.1)
deltaxzyz_figures.append(figGa)

def customizeDXZPlot(ax, fs, anchorx, anchory):
    cursor(hover=True)
    ax.grid(zorder=-1.0)
    ax.legend(loc='upper center', bbox_to_anchor=[anchorx, anchory], ncol=3, fontsize=fs)

figAN1, axAN1 = plt.subplots(1, 1, figsize=(15, 8))
dxdzdydzTBx, dxdzdydzTBy, events = getDxDzDyDzFor6HitsLEGO('TB', 90.0)
# Dump per-point list for debugging (one row per plotted point): x,y,event
try:
    points_csv = f"{report_stem}_hist_6hits_tb_dxdz_dydz_lego_plot_data.csv"
    with open(points_csv, 'w', encoding='utf-8') as _pf:
        _pf.write('# index,x,y,event_repr\n')
        for idx, (xv, yv, ev) in enumerate(zip(dxdzdydzTBx, dxdzdydzTBy, events)):
            _pf.write(f"{idx},{xv},{yv},{repr(ev)}\n")
    print(f"Wrote per-point dump: {points_csv}")
except Exception:
    pass
histAN1 = axAN1.hist2d(dxdzdydzTBx, dxdzdydzTBy, bins=(60, 60), cmap='jet')  # type: ignore
axAN1.figure.colorbar(histAN1[3], ax=axAN1)  # type: ignore
try:
    H, xedges, yedges = histAN1[0], histAN1[1], histAN1[2]
    try:
        import numpy as _np
        H_np, _, _ = _np.histogram2d(_np.array(dxdzdydzTBx), _np.array(dxdzdydzTBy), bins=(xedges, yedges))
        H = H_np
    except Exception:
        pass
    nbx = len(xedges) - 1
    nby = len(yedges) - 1
    bin_events = [[[] for _ in range(nby)] for _ in range(nbx)]
    try:
        import numpy as _np
        # Compute bin indices for all points using digitize so we match histogram2d
        x_idx = _np.digitize(_np.array(dxdzdydzTBx), xedges) - 1
        y_idx = _np.digitize(_np.array(dxdzdydzTBy), yedges) - 1
        for idx, ev in enumerate(events):
            xi = int(x_idx[idx])
            yi = int(y_idx[idx])
            # Handle digitize edge semantics: include points equal to the last edge
            if xi < 0 or yi < 0:
                if ev is None or (isinstance(ev, str) and ev.strip() == ''):
                    print(f"Diagnostic: empty event id in dxdzdydzTB loop at zip-index={idx} -> out-of-range bin candidates ({xi},{yi}); events_len={len(events)} dxboth_len={len(dxbothlayers)}")
                continue
            if xi >= nbx:
                if xi == nbx:
                    xi = nbx - 1
                else:
                    if ev is None or (isinstance(ev, str) and ev.strip() == ''):
                        print(f"Diagnostic: empty event id in dxdzdydzTB loop at zip-index={idx} -> out-of-range bin candidates ({xi},{yi}); events_len={len(events)} dxboth_len={len(dxbothlayers)}")
                    continue
            if yi >= nby:
                if yi == nby:
                    yi = nby - 1
                else:
                    if ev is None or (isinstance(ev, str) and ev.strip() == ''):
                        print(f"Diagnostic: empty event id in dxdzdydzTB loop at zip-index={idx} -> out-of-range bin candidates ({xi},{yi}); events_len={len(events)} dxboth_len={len(dxbothlayers)}")
                    continue
            if ev is None or (isinstance(ev, str) and ev.strip() == ''):
                print(f"Diagnostic: empty event id in dxdzdydzTB loop at zip-index={idx} -> bin({xi},{yi}); events_len={len(events)} dxboth_len={len(dxbothlayers)}")
            bin_events[xi][yi].append(ev)
    except Exception:
        pass
    out_csv = f"{report_stem}_hist_6hits_tb_dxdz_dydz_data.csv"
    missing_count = 0
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
                        dx = _np.array(dxdzdydzTBx)
                        dy = _np.array(dxdzdydzTBy)
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
    print(f"Failed to write 2D histogram data for 6-hits TB: {_e}")
axAN1.set_title(label='2D HISTOGRAM OF HITS DX/DZ - DY/DZ (TOP-BOTTOM) ' + runComments)
deltaxzyz_figures.append(figAN1)

def customizeFrequencyPlot(ax, fs, anchorx, anchory):
    cursor(hover=True)
    ax.grid(zorder=-1.0)
    ax.legend(loc='upper center', bbox_to_anchor=[anchorx, anchory], ncol=1, fontsize=fs)

figAN13, axAN13 = plt.subplots(1, 1, figsize=(10, 8))
# compute histogram for DX/DZ ratio
hist_ratio, edges_ratio, _, _ = compute_value_distributions(dxbothlayers, bins_x=100, bins_z=100)
# compute bin centers and widths (prefer numpy if available)
try:
    import numpy as _np
    edges_arr = _np.asarray(edges_ratio)
    centers = (edges_arr[:-1] + edges_arr[1:]) / 2.0
    widths = edges_arr[1:] - edges_arr[:-1]
    centers = centers.tolist()
    widths = widths.tolist()
except Exception:
    if len(edges_ratio) > 1:
        centers = [(edges_ratio[i] + edges_ratio[i + 1]) / 2.0 for i in range(len(edges_ratio) - 1)]
        widths = [edges_ratio[1] - edges_ratio[0]] * len(centers)
    else:
        centers = []
        widths = []
# plot as a bar chart consistent with other frequency plots
axAN13.bar(centers, hist_ratio, width=widths, color='seagreen', edgecolor='black', alpha=0.85,
            label='DX/DZ distribution ' + runComments)
axAN13.set_xlabel('DX / DZ')
axAN13.set_ylabel('Counts')
axAN13.set_title('Distribution of DX / DZ')
customizeFrequencyPlot(axAN13, 7, 0.5, 1.1)
deltaxzyz_figures.append(figAN13)

figAN14, axAN14 = plt.subplots(1, 1, figsize=(10, 8))
# compute histogram for DX/DZ ratio
hist_ratio14, edges_ratio14, _, _ = compute_value_distributions(dybothlayers, bins_x=100, bins_z=100)
# compute bin centers and widths (prefer numpy if available)
try:
    import numpy as _np
    edges_arr14 = _np.asarray(edges_ratio14)
    centers14 = (edges_arr14[:-1] + edges_arr14[1:]) / 2.0
    widths14 = edges_arr14[1:] - edges_arr14[:-1]
    centers14 = centers14.tolist()
    widths14 = widths14.tolist()
except Exception:
    if len(edges_ratio14) > 1:
        centers14 = [(edges_ratio14[i] + edges_ratio14[i + 1]) / 2.0 for i in range(len(edges_ratio14) - 1)]
        widths14 = [edges_ratio14[1] - edges_ratio14[0]] * len(centers14)
    else:
        centers14 = []
        widths14 = []

# plot as a bar chart consistent with other frequency plots
axAN14.bar(centers14, hist_ratio14, width=widths14, color='purple', edgecolor='black', alpha=0.85,
            label='DY/DZ distribution ' + runComments)
axAN14.set_xlabel('DY / DZ')
axAN14.set_ylabel('Counts')
axAN14.set_title('Distribution of DY / DZ')
customizeFrequencyPlot(axAN14, 7, 0.5, 1.1)
deltaxzyz_figures.append(figAN14)

figAN1ATAN, axAN1ATAN = plt.subplots(1, 1, figsize=(15, 8))
dxdzdydzTBATANx, dxdzdydzTBATANy, events = getDxDzDyDzFor6HitsLEGOATAN('TB', 90.0)
histAN1ATAN = axAN1ATAN.hist2d(dxdzdydzTBATANx, dxdzdydzTBATANy, bins=(60, 60), cmap='magma')  # type: ignore
axAN1ATAN.figure.colorbar(histAN1ATAN[3], ax=axAN1ATAN)  # type: ignore
try:
    H, xedges, yedges = histAN1ATAN[0], histAN1ATAN[1], histAN1ATAN[2]
    write_2d_histogram_event_csv(H, xedges, yedges, dxdzdydzTBATANx, dxdzdydzTBATANy, events, report_stem, 'hist_6hits_tb_dx_dz_atan')
except Exception as _e:
    print(f"Failed to write 2D histogram data for 6-hits TB atan: {_e}")
axAN1ATAN.set_title(label='ATAN 2D HISTOGRAM OF HITS DX/DZ - DY/DZ (TOP-BOTTOM) ' + runComments)
deltaxzyz_figures.append(figAN1ATAN)

plt.tight_layout()
stem = Path(input_file_name).stem
try:
    if range_suffix:
        stem = f"{stem}_{range_suffix}"
except NameError:
    pass

# Helper: determine whether a matplotlib Figure contains any plotted data.
def _figure_has_data(fig):
    try:
        for ax in fig.axes:
            for line in ax.get_lines():
                xd = getattr(line, 'get_xdata', lambda: [])()
                yd = getattr(line, 'get_ydata', lambda: [])()
                if xd is not None and yd is not None and len(xd) and len(yd):
                    return True
            for coll in getattr(ax, 'collections', []):
                try:
                    offsets = getattr(coll, 'get_offsets', lambda: [])()
                    if offsets is not None and len(offsets):
                        return True
                except Exception:
                    pass
            for im in getattr(ax, 'images', []):
                try:
                    arr = im.get_array()
                    if arr is not None:
                        try:
                            if getattr(arr, 'size', None) and arr.size:
                                return True
                        except Exception:
                            return True
                except Exception:
                    pass
            for p in getattr(ax, 'patches', []):
                try:
                    if hasattr(p, 'get_height'):
                        h = p.get_height()
                        if h is not None and h != 0:
                            return True
                    else:
                        return True
                except Exception:
                    return True
        return False
    except Exception:
        return True

deltaxzyz_filtered_figures = []
for fig in deltaxzyz_figures:
    if _figure_has_data(fig):
        deltaxzyz_filtered_figures.append(fig)
    else:
        try:
            plt.close(fig)
        except Exception:
            pass

filename1 = f"{stem}_dxzyz_charts.pdf"
pdf = matplotlib.backends.backend_pdf.PdfPages(filename1)
for i, figure in enumerate(deltaxzyz_filtered_figures):
    fig_to_save = figure if isinstance(figure, matplotlib.figure.Figure) else getattr(figure, 'figure', None)
    if fig_to_save is None:
        try:
            print(f"Skipping non-figure item when saving dxzyz charts: {repr(figure)}")
        except Exception:
            print("Skipping non-figure item when saving dxzyz charts (repr failed)")
        continue
    pdf.savefig(fig_to_save)
pdf.close()

# If requested, export tracking6 data to CSV after analysis completes
try:
    if export_tracking6_all:
        try:
            # include the same range suffix in the exported CSV filename
            export_tracking6_middle_hits_all(filename=f"{stem}_tracking6_middle_hits.csv")
        except Exception as _e:
            print(f"Failed exporting tracking6 CSVs: {_e}")
except NameError:
    # export_tracking6_all not defined (no args) — ignore
    pass
