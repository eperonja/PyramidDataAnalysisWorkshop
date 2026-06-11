PyramidDataAnalysisWorkshop
==========================

Small collection of scripts to parse and analyze pyramid-detector data files and to produce charts.

Contents
--------
- `main.py` — entry point that runs the three stages in sequence: `read_pyramid_data.py`, `analyze_pyramid_data.py`, `plot_pyramid_data_workshop.py`.
- `read_pyramid_data.py` — reads the input data file and prepares in-memory structures.
- `analyze_pyramid_data.py` — performs analysis on the in-memory data (tracks, deltas, filters).
- `plot_pyramid_data_workshop.py` — creates charts/plots from the analysis results.
- `config/` — configuration files required by the scripts (`adcmap.txt`, `geometry_header.txt`, `pedestal.txt`).
- Example data files included (e.g. `Run1100_list_six_hits_converted.txt`).

Requirements
------------
- Python 3.8+ (3.8, 3.9, 3.10 are known to work)
- pip
- The project contains a `requirements.txt` with core runtime dependencies. The scripts also use `python-dateutil` (imported as `dateutil`) which may not be listed in `requirements.txt` depending on the copy you have.

Install
-------
Recommended: create and use a virtual environment. On macOS / bash:

```bash
# create a venv in the project (one-time)
python3 -m venv .venv

# activate it (each new shell)
source .venv/bin/activate

# upgrade pip and install requirements
pip install --upgrade pip
pip install -r requirements.txt

# install dateutil if not present
pip install python-dateutil
```

If you prefer to install globally (not recommended) run the pip commands without activating a venv.

Usage
-----
Run the pipeline from `main.py`. The script expects an input data file and optional channel-range arguments.

Basic usage:

```bash
python main.py <input_file>
```

Examples (uses the CLI argument parsing implemented in `main.py`):

```bash
# run with default channel ranges
python main.py Run1100_list_six_hits_converted.txt

# restrict X channels to 10-30 and Y channels to 5-40
python main.py Run1100_list_six_hits_converted.txt X=10-30 Y=5-40

# set ranges per board, e.g. X0, Y2
python main.py Run1100_list_six_hits_converted.txt X0=1-28 Y2=1-48

# export additional tracking output
python main.py Run1100_list_six_hits_converted.txt --export-tracking6-all
```
