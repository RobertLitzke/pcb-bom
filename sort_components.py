import argparse, re, sys
from functools import cmp_to_key

# Regexes to match different lines and identify values.
resistors_re = re.compile(r"^(R\d+|RLED|LEDR|RPD|CLR)?\s(\d+[KkMR]\d*)\s?(.*)?")
resistor_value_re = re.compile(r"\D*\d*\s?(\d+[KkMR]\d*).*")

capacitors_re = re.compile(r"^(C\d+)?\s(\d+\.?\d?[uUnNpPF]+\d*)\s?(.*)?")
capacitor_value_re = re.compile(r"\D*\d*\s?(\d+\.?\d?[uUnNpPF]+\d*)\s?(.*)?")

diodes_re = re.compile(
	r"^((?:D\d+|LED_?\w*))?\s(\d*(?:1N|1S|V|MA|D|LED )\d*\w?|(?:\dmm )?\w*(?:Indicator|Red|Green|green|Yellow)(?:(?: \dmm)? LED)?|GE|BAT\d*)\s?(.*)?"
)
diode_value_re = re.compile(r"\D*\d*\s?(\d*(?:1N|1S|V|MA|D|LED )\d*\w?|(?:\dmm )?\w*(?:Indicator|Red|red|Green|green|Yellow)(?:(?: \dmm)? LED)?|GE|BAT\d*).*")

ics_re = re.compile(r"^(IC\d+)?\s(\d*(?:RC|CD|AD|[TLNV]|FV|JRC|PT|OPA|MN|SPIN FV-1|BTDR-\dH.*)\d*\w*)\s?(.*)?")
ic_value_re = re.compile(r"\D*\d*\s?(\d*(?:RC|CD|AD|[TLNV]|FV|JRC|PT|OPA|MN|SPIN FV-1|BTDR-\dH.*)\d*\w*).*")

sockets_re = re.compile(r"^(IC\d+-S)?\s(DIP-\d+ socket)\s?(.*)?")
socket_value_re = re.compile(r"\D*\d*-S\s?(DIP-\d+ socket)\s?(.*)?")

pots_re = re.compile(
	r"^((?:GAIN|TONE|LEVEL|RATE|DEPTH|LAG|BLEND|TRIM|VOLUME|SUSTAIN|HARMONICS|BALANCE|OCTAVE|FUZZ|VOICE|DRIVE|PRES|RANGE|BOOST|HEAT|BEFORE|BIAS|DIRT|MORE|MIX|VOL|MID|SWEEP|PRESENCE|PUSH|TRIM1|TRIM2|TRIM3|TRIM|FUZZ1|FUZZ2|SHIFT|TONE1|TONE2|LEVEL1|LEVEL2|FAT|BODY|BRITE|HICUT|AFTER|OUTPUT|BEFOR|SPEED|AGE|DRIVE|VOL|TONE|TREBLE|DISPERSE|DEFLECT|DIMINISH|DENSITY|DURATION|DILUTE|DELAY|REPEAT|RES|FILTER|DISTORTION|AMPLITUDE|TIME|REPEATS|SHAPE|TREBLE|BASS|DECAY|VOICE|BANDWIDTH|GAIN_A|GAIN_B|ATMOSPHERE|ODC|SPECT|COMP|VACT|LO CUT|BONE|INTENSITY|THROB|FEEDBACK|TRACKING|POT|OSC|MOOD|SQUARE|SUB|GRAVITY|SPACE|CUT|WAVE)\d?\.?)?\s([ABWC]?\d+[MKkABCW]*(?: TRIM| trim| DUAL| dual)?)\s?(.*)?"
)
pot_value_re = re.compile(r"\D*\d*\s([ABCW]?\d+[MKkABCW]*(?: TRIM| trim| DUAL| dual)?).*")

switches_re = re.compile(
	r"^(SW\d|MODE|SHAPE|BRIGHT|BUFFER|GTRBASS|CONTOUR|LENGTH|VOICE|BANDWIDTH|PV|RANGE|OSC|SUB-ROOT|OSC-ROOT|OSC-SW|SUB-SW|GLIDE)?\s*((?:(?:D|S)?P(?:D|S)?T\s*|\(?[ONnFf/]+\)?|Toggle switch,?\s*|Toggle\s*|2-position\s*|Mini 1P8T|2P4T Mini Rotary Switch|1P8T Mini Rotary|DIP\d)+)"
)
switch_value_re = re.compile(
	r"(?:[\w-])*\d*\s?((?:(?:D|S)?P(?:D|S)?T\s*|\(?[ONnFf/]+\)?|Toggle switch,?\s*|Toggle\s*|2-position\s*|Mini 1P8T|2P4T Mini Rotary Switch|1P8T Mini Rotary|DIP\d)+)"
)

transistors_re = re.compile(r"^(Q\d+)?\s((?:MPF|NPN|BC|J|BS|AC|MPSA|PF|PN|1T)\d*\*?|\d*[2N]+\d*A?)\s?(.*)?")
transistor_value_re = re.compile(r"\D*\d*\s?((?:MPF|NPN|BC|J|BS|AC|MPSA|PF|PN|1T)\d*\*?|\d*[2N]+\d*A?).*")

project_re = re.compile(r"^\*([\s\w\d]+)\s(http.*)")
part_type_re = re.compile(
	r".*(RESISTORS\s?(\((?:1/4W|1/8W)\))?|CAPACITORS|TRANSISTORS|DIODES|SWITCHES|POTS|POTENTIOMETERS|INTEGRATED CIRCUITS|SEMICONDUCTORS|OPTICAL|LEDS|LDRS|CRYSTAL OSCILLATORS|TOGGLE SWITCHES|ROTARY SWITCHES).*",
	re.IGNORECASE,
)

# Regex the identifies units in capacitors, to help standardize (100u vs 100UF).
capacitor_unit_re = re.compile(r"(\d*\.?\d*)(\w)F?\d*")

# Regex that identifies tapers, to help standardize (A50K vs 50KA).
pot_taper = re.compile(r"([ABCW])?\d*[MkK]?([ABCW])?")

# Handles periods in the value, and strips out "F" for consistency.
def standardize_capacitor(value):
	if "." in value:
		letter = capacitor_unit_re.match(value)[2]
		value = value.replace(letter, "")
		value = value.replace(".", letter)
	value = value.replace("F", "")
	value = value.replace("f", "")
	return str.upper(value)

# Handles various inconsistencies in switches
def standardize_switch(value):
	value = value.replace("(", "")
	value = value.replace(")", "")
	value = value.replace("TOGGLE ", "")
	return str.upper(value)

# Handles the taper at start or end, moving it to start.
def standardize_pot(value):
	taper = pot_taper.match(value)
	if taper[2] is not None:
		value = taper[2] + value[:-1]
	return str.upper(value)

# The simplest standardization function.
def capitalize(value):
	return str.upper(value)

# To the extent it is shared, standardize the capacitor type. The description
# is the last part of the capacitor line and when present tends to say the type.
def determine_capacitor_type(description):
	if description is None or str.strip(description) == "":
		return None
	if re.match(r".*Electrolytic.*", description, re.IGNORECASE):
		return "(ELECTROLYTIC)"
	if re.match(r".*Film.*", description, re.IGNORECASE):
		return "(FILM)"
	if re.match(r".*(MLCC|Ceramic).*", description, re.IGNORECASE):
		return "(CERAMIC)"
	print("Unknown cap type " + description)
	return None

# Determines resistor type from the description (the wattage).
def determine_resistor_type(description):
	if description is None or str.strip(description) == "":
		return None
	if re.match(r".*1/4W.*", description, re.IGNORECASE):
		return "(1/4W)"
	if re.match(r".*1/8W.*", description, re.IGNORECASE):
		return "(1/8W)"
	print("Unknown resistor type " + description)
	return None

# Now the functions which actually process individual lines.

def process_part_type(line, rows, value_prefix, separator):
	rows.append(f"{value_prefix}{separator}{part_type_re.match(line).groups()[0]}")

def process_project_name(line, rows, value_prefix, separator):
	rows.append(f"{value_prefix}{separator}{project_re.match(line).groups()[0]}{separator}{project_re.match(line).groups()[1]}")

def process_simple(line, rows, totals, line_regex, value_regex, current_project, value_prefix, separator, consolidation_fn):
	line_regex_result = line_regex.match(line)
	rows.append(f"{separator.join([group for group in line_regex_result.groups() if group != ''])}")
	value_regex_result = f"{value_prefix}{separator}{consolidation_fn(value_regex.match(line).groups()[0])}"
	if value_regex_result in totals:
		if current_project in totals[value_regex_result]["ProjectCounts"]:
			totals[value_regex_result]["ProjectCounts"][current_project] +=  1
		else:
			totals[value_regex_result]["ProjectCounts"][current_project] = 1
	else:
		totals[value_regex_result] = {
			"name": value_regex.match(line).groups()[0],
			"ProjectCounts": {current_project: 1}
		}

# The main function that processes each row.
def process(str_in, rows, totals, projects, separator):
	lines = str_in.split("\n")
	current_project = "Unprocessed"
	current_part_type_annotation = None
	for line in lines:
		if line.strip() == "":
			continue
		project_match = project_re.match(line)
		if project_match:
			process_project_name(line, rows, "\nPROJECT", separator)
			projects.append(
				f"{project_match.groups()[0]}{separator}{project_match.groups()[1]}"
			)
			current_project = project_match.groups()[0]
			continue
		part_type_match = part_type_re.match(line)
		if part_type_match:
			process_part_type(line, rows, "PART CLASS", separator)
			if part_type_match.groups()[1] is not None:
				current_part_type_annotation = part_type_match.groups()[1]
			else:
				current_part_type_annotation = None
			continue
		resistor_match = resistors_re.match(line)
		capacitor_match = capacitors_re.match(line)
		ic_match = ics_re.match(line)
		socket_match = sockets_re.match(line)
		diodes_match = diodes_re.match(line)
		transistors_match = transistors_re.match(line)
		pots_match = pots_re.match(line)
		switches_match = switches_re.match(line)
		
		# Socket match should come before IC match.
		if socket_match:
			process_simple(
				line, rows, totals, sockets_re, socket_value_re, current_project, "SOCKET", separator,
				capitalize
			)
		elif ic_match:
					process_simple(
						line, rows, totals, ics_re, ic_value_re, current_project, "IC", separator,
				capitalize
					)
		elif diodes_match:
			process_simple(
				line, rows, totals, diodes_re, diode_value_re, current_project, "DIODE", separator,
				capitalize
			)
		elif pots_match:
			process_simple(
				line, rows, totals, pots_re, pot_value_re, current_project, "POT", separator,
				standardize_pot
			)
		elif transistors_match:
			process_simple(
				line,
				rows,
				totals,
				transistors_re,
				transistor_value_re,
				current_project,
				"TRANSISTOR",
				separator,
				capitalize
			)
		elif switches_match:
			print(line)
			process_simple(
				line, rows, totals, switches_re, switch_value_re, current_project, "SWITCH", separator,
				standardize_switch
			)
		elif resistor_match:
			specific_type = determine_resistor_type(resistor_match.groups()[-1])
			resistor_label = "RESISTOR (1/4W)"
			if specific_type is not None:
				resistor_label = f"RESISTOR {specific_type}"
			elif current_part_type_annotation is not None:
				resistor_label = f"RESISTOR {current_part_type_annotation}"
			process_simple(
				line,
				rows,
				totals,
				resistors_re,
				resistor_value_re,
				current_project, 
				resistor_label,
				separator,
				capitalize
			)
		elif capacitor_match:
			cap_type = determine_capacitor_type(capacitor_match.groups()[-1])
			capacitor_label = "CAPACITOR" if cap_type is None else f"CAPACITOR {cap_type}"
			process_simple(
				line,
				rows,
				totals,
				capacitors_re,
				capacitor_value_re,
				current_project,
				capacitor_label,
				separator,
				standardize_capacitor
			)
		else:
			rows.append(f"{line} (unprocessed)")
			totals["UNPROCESSED"]["ProjectCounts"]["Unknown"] += 1

# Functions that write different types of outputs.

# Outputs the list of parts in the same order they were input, but now standardized.
def output_parts(parts, filename):
	out = ""
	for item in parts:
		out += f"{item}\n"
	f = open(filename, "w")
	f.write(out)
	f.close()

# Outputs totals. Will sort by type and value.
def output_totals(totals, separator, filename, parts_url):
	list = []
	for key, value in totals.items():
		total_count = sum(value["ProjectCounts"].values())
		projects = "/".join(f"{i[0]}({i[1]})" for i in value["ProjectCounts"].items())
		if parts_url == "":
			list.append(f"{key}{separator}{total_count}{separator}{projects}")
		else:
			list.append(f"{key}{separator}{total_count}{separator}{projects}{separator}{parts_url.replace('%s',value["name"])}")
	list = sorted(list, key=cmp_to_key(compare_total))
	out = ""
	for item in list:
		out += f"{item}\n"
	f = open(filename, "w")
	f.write(out)
	f.close()

# Comparator for totals. Will do the following:
# * Sort capacitors by ascending value. Not sorting by type because most projects have multiple.
# * Sort resistors by type (1/4W and 1/8W) and then ascending value. Sorting by type because most
# 		projects just have a single type
# * Otherwise sort alphabetically.
def compare_total(a, b):
	# Super messy, decode the totals. Should just have an object probably.
	cap_total_re = r"CAPACITOR(?: \((?:FILM|CERAMIC|ELECTROLYTIC)\))?\|(.*)\|.*\|.*"
	a_cap = re.match(cap_total_re, a)
	b_cap = re.match(cap_total_re, b)
	if a_cap is not None and b_cap is not None:
		a_value = capacitor_to_value(a_cap)
		b_value = capacitor_to_value(b_cap)
		return 1 if a_value > b_value else -1 if a_value < b_value else 0
	
	resistor_total_re = r"RESISTOR(?: \((1/4W|1/8W)\))?\|(.*)\|.*\|.*"
	a_res = re.match(resistor_total_re, a)
	b_res = re.match(resistor_total_re, b)
	if a_res is not None and b_res is not None and a_res.groups()[0] == b_res.groups()[0]:
		a_value = resistor_to_value(a_res)
		b_value = resistor_to_value(b_res)
		return 1 if a_value > b_value else -1 if a_value < b_value else 0
	return 1 if a > b else -1 if a < b else 0

# Extract the actual fahrads (picofahrads) for the capacitor, for numeric sorting.
def capacitor_to_value(cap):
	cap_value_re = r"(\d+)([NUP])(\d*)"
	match = re.match(cap_value_re, cap.groups()[0])
	value = int(match.groups()[0])
	after_decimal = 0
	if match.groups()[-1] is not None and str.strip(match.groups()[-1]) != "":
		after_decimal = int(match.groups()[-1]) / (10 * len(match.groups()[-1]))
	value = value + after_decimal
	return value * (1000000 if match.groups()[1] == "U" else 1000 if match.groups()[1] == "N" else 1)

# Extract the actual number of ohms for a resistor, for numeric sorting.
def resistor_to_value(res):
	resistor_value_re = r"(\d+)([KRM])(\d*)"
	match = re.match(resistor_value_re, res.groups()[1])
	value = int(match.groups()[0])
	after_decimal = 0
	if match.groups()[-1] is not None and str.strip(match.groups()[-1]) != "":
		after_decimal = int(match.groups()[-1]) / (10 * len(match.groups()[-1]))
	value = value + after_decimal
	return value * (1000000 if match.groups()[1] == "M" else 1000 if match.groups()[1] == "K" else 1)

# Just outputs the project list.
def output_projects(projects, filename):
	out = ""
	for project in projects:
		out += project + "\n"
	f = open(filename, "w")
	f.write(out)
	f.close()


def main(in_file, parts_file, totals_file, projects_file, parts_url, separator):
	parts = []
	totals = {"UNPROCESSED": {"name": "Unprocessed", "ProjectCounts": {"Unknown": 0}}}
	projects = []
	f = open(in_file, "r")
	str_in = f.read()
	process(str_in, parts, totals, projects, separator)
	output_parts(parts, parts_file)
	output_totals(totals, separator, totals_file, parts_url)
	output_projects(projects, projects_file)


if __name__ == "__main__":
	parser = argparse.ArgumentParser()
	parser.add_argument("--in_file", help="The file to process")
	parser.add_argument(
		"--parts_file",
		help="Filename to outputs a list of parts that can be ingested into a spreadsheet",
		default="parts.txt",
	)
	parser.add_argument(
		"--totals_file",
		help="Filename to output a tabulated list of totals",
		default="totals.txt",
	)
	parser.add_argument(
		"--projects_file",
		help="Filename to output a tabulated list of projects",
		default="projects.txt",
	)
	parser.add_argument(
		"--separator",
		help="Character to use to separate columns in output",
		default="|",
	)
	parser.add_argument(
		"--parts_url",
		help="A url with query parameter `%s` to replace with the component, like a Chrome custom search engine.",
		default="",
	)
	args = parser.parse_args()
	main(
		args.in_file,
		args.parts_file,
		args.totals_file,
		args.projects_file,
		args.parts_url,
		args.separator,
	)
