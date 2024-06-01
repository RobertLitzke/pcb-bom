import re
import sys

resistors_re = re.compile(r'^(R\d+|RLED)?\s(\d+[KMR]\d?)\s?(.*)?')
resistor_value_re = re.compile(r'\D*\d*\s?(\d+[KMR]\d?).*')

capacitors_re = re.compile(r'^(C\d+)?\s(\d+[uUnNpP])\s?(.*)?')
capacitor_value_re = re.compile(r'\D*\d*\s?(\d+[uUnNpP])\s?(.*)?')

diodes_re = re.compile(r'^(D\d+)?\s(\d*[1N|V]\d*|\dmm Red(?: LED)?|GE|BAT\d*)\s?(.*)?')
diode_value_re = re.compile(r'\D*\d*\s?(\d*[1N|V]\d*|\dmm Red(?: LED)?|GE|BAT\d*).*')

ics_re = re.compile(r'^(IC\d+)?\s(\d*(?:RC|CD|AD|[TLNV])\d*\w*)\s?(.*)?')
ic_value_re = re.compile(r'\D*\d*\s?(\d*(?:RC|CD|AD|[TLNV])\d*\w*).*')

pots_re = re.compile(r'^(GAIN|TONE|LEVEL|RATE|DEPTH|LAG|BLEND|TRIM|VOLUME|SUSTAIN|HARMONICS|BALANCE|OCTAVE|FUZZ|VOICE|DRIVE|PRES|RANGE|BOOST|HEAT|BIAS|DIRT|MORE)?\s([ABWC]?\d+[MK])\s?(.*)?')
pot_value_re = re.compile(r'\D*\d*\s([ABCW]?\d+[MK]).*')

switches_re = re.compile(r'^(SW\d|MODE|SHAPE)?\s((?:[ONF/]+\s?Toggle switch, )?SPDT\s?(?:2-position)?\s?\([ONF/]+\))\s?(.*)?')
switch_value_re = re.compile(r'\D*\d*\s?((?:[ONF/]+\s?Toggle switch, )?SPDT\s?(?:2-position)?\s?\([ONF/]+\)).*')

transistors_re = re.compile(r'^(Q\d+)?\s((?:MPF|NPN|BC)\d*\*?|\d*[2N]\d*A?|\d)\s?(.*)?')
transistor_value_re = re.compile(r'\D*\d*\s?((?:MPF|NPN|BC)\d*\*?|\d*[2N]\d*A?|\d).*')

pedal_re = re.compile(r'^\*([\s\w\d]+)\s(http).*')
part_type_re = re.compile(r'.*(RESISTORS\s?(?:\(1/4W\))?|CAPACITORS|TRANSISTORS|DIODES|SWITCHES|POTS|POTENTIOMETERS|INTEGRATED CIRCUITS|SEMICONDUCTORS).*', re.IGNORECASE)

def process_part_type(line, out, value_prefix):
	out += "\n" + value_prefix + part_type_re.match(line).groups()[0]
	return out

def process_pedal_name(line, out, value_prefix):
	out += "\n" + value_prefix + pedal_re.match(line).groups()[0]
	return out

def process_simple(line, out, totals, line_regex, value_regex, value_prefix):
	line_regex_result = line_regex.match(line)
	out += f"\n{'|'.join(line_regex_result.groups())}"
	value_regex_result = value_prefix + value_regex.match(line).groups()[0]
	if value_regex_result in totals:
		totals[value_regex_result] += 1
	else:
		totals[value_regex_result] = 1
	return [out, totals]

def process(str_in, out, totals, pedals):
	lines = str_in.split('\n')
	for line in lines:
		#print(line)
		pedal_match = pedal_re.match(line)
		if pedal_match:
			out = process_pedal_name(line, out, 'PEDAL: ')
			pedals.append(pedal_match.groups()[0])
			continue
		part_type_match = part_type_re.match(line)
		if part_type_match:
			out = process_part_type(line, out, 'PART CLASS: ')
			continue
		resistor_match = resistors_re.match(line)
		capacitor_match = capacitors_re.match(line)
		ic_match = ics_re.match(line)
		diodes_match = diodes_re.match(line)
		transistors_match = transistors_re.match(line)
		pots_match = pots_re.match(line)
		switches_match = switches_re.match(line)

		if ic_match:
			[out, totals] = process_simple(line, out, totals, ics_re, ic_value_re, 'IC|')
		elif diodes_match:
			[out, totals] = process_simple(line, out, totals, diodes_re, diode_value_re, 'DIODE|')
		elif pots_match:
			[out, totals] = process_simple(line, out, totals, pots_re, pot_value_re, 'POT|')
		elif transistors_match:
			[out, totals] = process_simple(line, out, totals, transistors_re, transistor_value_re, 'TRANSISTOR|')
		elif switches_match:
			[out, totals] = process_simple(line, out, totals, switches_re, switch_value_re, 'SWITCH|')
		elif resistor_match:
			[out, totals] = process_simple(line, out, totals, resistors_re, resistor_value_re, 'RESISTOR|')
		elif capacitor_match:
			[out, totals] = process_simple(line, out, totals, capacitors_re, capacitor_value_re, 'CAPACITOR|')
		else:
			out += f"\n{line} (unprocessed)"
	return [out,totals]

def print_part_counts(totals):
	list = [f"{key}|{value}" for key, value in totals.items()]
	list.sort()
	for item in list:
		print(item,)

def main():
	out = ''
	totals = {}
	pedals = []
	f = open(sys.argv[1], "r")
	str_in = f.read()
	[out,totals] = process(str_in, out, totals, pedals)
	print(out)
	print("TOTALS",)
	print_part_counts(totals)
	print("PEDALS")
	for pedal in pedals:
		print(pedal,)

if __name__ == "__main__":
	main()