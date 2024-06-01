import argparse, re, sys

resistors_re = re.compile(r"^(R\d+|RLED)?\s(\d+[KMR]\d*)\s?(.*)?")
resistor_value_re = re.compile(r"\D*\d*\s?(\d+[KMR]\d*).*")

capacitors_re = re.compile(r"^(C\d+)?\s(\d+[uUnNpP])\s?(.*)?")
capacitor_value_re = re.compile(r"\D*\d*\s?(\d+[uUnNpP])\s?(.*)?")

diodes_re = re.compile(
    r"^(D\d+)?\s(\d*[1N|V]\d*\w?|\dmm Red(?: LED)?|GE|BAT\d*)\s?(.*)?"
)
diode_value_re = re.compile(r"\D*\d*\s?(\d*[1N|V]\d*\w?|\dmm Red(?: LED)?|GE|BAT\d*).*")

ics_re = re.compile(r"^(IC\d+)?\s(\d*(?:RC|CD|AD|[TLNV])\d*\w*)\s?(.*)?")
ic_value_re = re.compile(r"\D*\d*\s?(\d*(?:RC|CD|AD|[TLNV])\d*\w*).*")

pots_re = re.compile(
    r"^(GAIN|TONE|LEVEL|RATE|DEPTH|LAG|BLEND|TRIM|VOLUME|SUSTAIN|HARMONICS|BALANCE|OCTAVE|FUZZ|VOICE|DRIVE|PRES|RANGE|BOOST|HEAT|BIAS|DIRT|MORE)?\s([ABWC]?\d+[MK])\s?(.*)?"
)
pot_value_re = re.compile(r"\D*\d*\s([ABCW]?\d+[MK]).*")

switches_re = re.compile(
    r"^(SW\d|MODE|SHAPE)?\s((?:[ONF/]+\s?Toggle switch, )?SPDT\s?(?:2-position)?\s?\([ONF/]+\))\s?(.*)?"
)
switch_value_re = re.compile(
    r"\D*\d*\s?((?:[ONF/]+\s?Toggle switch, )?SPDT\s?(?:2-position)?\s?\([ONF/]+\)).*"
)

transistors_re = re.compile(r"^(Q\d+)?\s((?:MPF|NPN|BC)\d*\*?|\d*[2N]\d*A?|\d)\s?(.*)?")
transistor_value_re = re.compile(r"\D*\d*\s?((?:MPF|NPN|BC)\d*\*?|\d*[2N]\d*A?|\d).*")

project_re = re.compile(r"^\*([\s\w\d]+)\s(http.*)")
part_type_re = re.compile(
    r".*(RESISTORS\s?(?:\(1/4W\))?|CAPACITORS|TRANSISTORS|DIODES|SWITCHES|POTS|POTENTIOMETERS|INTEGRATED CIRCUITS|SEMICONDUCTORS).*",
    re.IGNORECASE,
)

def process_part_type(line, rows, value_prefix, separator):
    rows.append(f"{value_prefix}{separator}{part_type_re.match(line).groups()[0]}")


def process_project_name(line, rows, value_prefix, separator):
    rows.append(f"{value_prefix}{separator}{project_re.match(line).groups()[0]}{separator}{project_re.match(line).groups()[1]}")


def process_simple(line, rows, totals, line_regex, value_regex, value_prefix, separator):
    line_regex_result = line_regex.match(line)

    rows.append(f"{separator.join([group for group in line_regex_result.groups() if group != ''])}")
    value_regex_result = (
        f"{value_prefix}{separator}{value_regex.match(line).groups()[0]}"
    )
    if value_regex_result in totals:
        totals[value_regex_result] += 1
    else:
        totals[value_regex_result] = 1


def process(str_in, rows, totals, projects, separator):
    lines = str_in.split("\n")
    for line in lines:
        project_match = project_re.match(line)
        if project_match:
            process_project_name(line, rows, "\nPROJECT", separator)
            projects.append(
                f"{project_match.groups()[0]}{separator}{project_match.groups()[1]}"
            )
            continue
        part_type_match = part_type_re.match(line)
        if part_type_match:
            process_part_type(line, rows, "PART CLASS", separator)
            continue
        resistor_match = resistors_re.match(line)
        capacitor_match = capacitors_re.match(line)
        ic_match = ics_re.match(line)
        diodes_match = diodes_re.match(line)
        transistors_match = transistors_re.match(line)
        pots_match = pots_re.match(line)
        switches_match = switches_re.match(line)

        if ic_match:
            process_simple(
                line, rows, totals, ics_re, ic_value_re, "IC", separator
            )
        elif diodes_match:
            process_simple(
                line, rows, totals, diodes_re, diode_value_re, "DIODE", separator
            )
        elif pots_match:
            process_simple(
                line, rows, totals, pots_re, pot_value_re, "POT", separator
            )
        elif transistors_match:
            process_simple(
                line,
                rows,
                totals,
                transistors_re,
                transistor_value_re,
                "TRANSISTOR",
                separator,
            )
        elif switches_match:
            process_simple(
                line, rows, totals, switches_re, switch_value_re, "SWITCH", separator
            )
        elif resistor_match:
            process_simple(
                line,
                rows,
                totals,
                resistors_re,
                resistor_value_re,
                "RESISTOR",
                separator,
            )
        elif capacitor_match:
            process_simple(
                line,
                rows,
                totals,
                capacitors_re,
                capacitor_value_re,
                "CAPACITOR",
                separator,
            )
        else:
            rows.append(f"{line} (unprocessed)")
            totals["UNPROCESSED"] += 1


def output_parts(parts, filename):
    print(
        "====PARTS====",
    )
    out = ""
    for item in parts:
        out += f"{item}\n"
    print(out)
    f = open(filename, "w")
    f.write(out)
    f.close()


def output_totals(totals, separator, filename):
    list = [f"{key}{separator}{value}" for key, value in totals.items()]
    list.sort()
    out = ""
    for item in list:
        out += f"{item}\n"
    print(
        "====TOTALS====",
    )
    print(out)
    f = open(filename, "w")
    f.write(out)
    f.close()


def output_projects(projects, filename):
    out = ""
    print(
        "====PROJECTS====",
    )
    for project in projects:
        out += project + "\n"
    print(out)
    f = open(filename, "w")
    f.write(out)
    f.close()


def main(in_file, parts_file, totals_file, projects_file, separator):
    parts = []
    totals = {"UNPROCESSED": 0}
    projects = []
    f = open(in_file, "r")
    str_in = f.read()
    process(str_in, parts, totals, projects, separator)
    output_parts(parts, parts_file)
    output_totals(totals, separator, totals_file)
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
    args = parser.parse_args()
    main(
        args.in_file,
        args.parts_file,
        args.totals_file,
        args.projects_file,
        args.separator,
    )
