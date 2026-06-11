
"""Start the analysis pipeline from here.
This script parses the command-line options (same semantics as the original
single-file script) and then executes the three module files in the correct
order inside a shared namespace so they can rely on the same globals.
"""
import sys
import re
import os
from pathlib import Path

def resource_path(relative_path: str) -> str:
	import sys as _sys, os as _os
	if getattr(_sys, 'frozen', False):
		base_path = getattr(_sys, '_MEIPASS', os.path.dirname(__file__))
	else:
		base_path = _os.path.dirname(__file__)
	return _os.path.join(base_path, relative_path)
#end of resource_path

def parse_args(argv):
	if len(argv) < 2:
		print("Usage: python main.py <input_file> [X=..] [Y=..] [X0=..] [Y2=..] [--export-tracking6-all]")
		sys.exit(1)
	input_file_name = argv[1]
	x_ranges = [None, None, None]
	y_ranges = [None, None, None]
	export_tracking6_all = False
	for arg in argv[2:]:
		if arg == '--export-tracking6-all':
			export_tracking6_all = True
		mglobx = re.match(r'X=(\d+)-(\d+)', arg)
		mgloby = re.match(r'Y=(\d+)-(\d+)', arg)
		if mglobx:
			vmin = int(mglobx.group(1)); vmax = int(mglobx.group(2))
			x_ranges = [(vmin, vmax), (vmin, vmax), (vmin, vmax)]
		if mgloby:
			vmin = int(mgloby.group(1)); vmax = int(mgloby.group(2))
			y_ranges = [(vmin, vmax), (vmin, vmax), (vmin, vmax)]
	for arg in argv[2:]:
		mxi = re.match(r'X([0-2])=(\d+)-(\d+)', arg)
		myi = re.match(r'Y([0-2])=(\d+)-(\d+)', arg)
		if mxi:
			idx = int(mxi.group(1)); x_ranges[idx] = (int(mxi.group(2)), int(mxi.group(3)))
		if myi:
			idx = int(myi.group(1)); y_ranges[idx] = (int(myi.group(2)), int(myi.group(3)))

	def _range_str(r):
		return 'ALL' if r is None else f"{r[0]}-{r[1]}"

	runComments = f"Using channel ranges: X0={_range_str(x_ranges[0])} X1={_range_str(x_ranges[1])} X2={_range_str(x_ranges[2])} Y0={_range_str(y_ranges[0])} Y1={_range_str(y_ranges[1])} Y2={_range_str(y_ranges[2])} "

	def _build_range_suffix(x_ranges, y_ranges):
		parts = []
		for i in range(3):
			parts.append(f"X{i}-" + (_range_str(x_ranges[i])))
		for i in range(3):
			parts.append(f"Y{i}-" + (_range_str(y_ranges[i])))
		return "_".join(parts)

	range_suffix = _build_range_suffix(x_ranges, y_ranges)

	return {
		'input_file_name': input_file_name,
		'x_ranges': x_ranges,
		'y_ranges': y_ranges,
		'export_tracking6_all': export_tracking6_all,
		'runComments': runComments,
		'range_suffix': range_suffix,
	}
#end of parse_args

def exec_file_in_namespace(path: Path, namespace: dict):
	src = path.read_text(encoding='utf-8')
	code = compile(src, str(path), 'exec')
	exec(code, namespace)
#end of exec_file_in_namespace

def main(argv=None):
	if argv is None:
		argv = sys.argv
	params = parse_args(argv)
	ns = {
		'__name__': '__main__',
		'__file__': str(Path(__file__).resolve()),
		'resource_path': resource_path,
	}
	# inject parsed CLI params into namespace (so modules can use them directly)
	ns.update(params)
	base = Path(__file__).parent
	files = ['read_pyramid_data.py', 'analyze_pyramid_data.py', 'plot_pyramid_data_workshop.py']
	for fname in files:
		p = base / fname
		if not p.exists():
			print(f"Expected file missing: {p}")
			sys.exit(1)
		print(f"Running: {p.name}")
		try:
			exec_file_in_namespace(p, ns)
		except Exception as e:
			print(f"Error while executing {p.name}: {e}")
			raise
#end of main

if __name__ == '__main__':
	main()

