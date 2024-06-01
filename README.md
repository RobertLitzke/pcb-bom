# PCB Bill of Materials (pcb-bom)
Utility for tabulating and bulk-ordering electronic components from poorly-structured lists of data (e.g. PedalPCB component lists). It was created for guitar pedal component calculations.

## What does it do?

You have list of random electronic parts you want to order. It may be poorly structured, not have columns, and it may have many repeated elements. Perhaps it's a list for many projects at once, increasing the risk of duplicate entries.

You do the following:
* Put any components into a raw text file, according to the format below.
* Run `python sort_components.py -in_file=<text file name>`
* You receive the following files:
  * *Parts list* - The parts list, with delimiters between columns, suitable for pasting into a spreadsheet.
  * *Totals* - The total number of components of each type, across all projects.
  * *Projects* - A list of just the project names, in case you want to store them somewhere.

## What format does it support?

In short this was designed to take parts lists from PedalPCB. You can see an overall example of a working input in `examples/input.txt`. A list of the following format is currently supported:

### Electrical components
`<Component name in project> <Component specification> <Optional Description>`

* *Component name in project* - This would be things like `R1` or `IC2`
* *Component specification* - This would be things like `4K7` or `100u`
* *Optional description* - Any additional text

Each part must be on its own line. Here are some examples:

```
R14 100K
C100 10p Can be a ceramic capacitor 
D5 1N4148
LEVEL B100K Should use 16mm split shaft
```

### Other information

You can also specify projects:

`*<Project name> <URL>`

The project row must start with an asterisk and must include a URL at the end. The URL can be anything. Here are some examples:

```
*Greengage https://docs.pedalpcb.com/project/Greengage.pdf
*Shika https://docs.pedalpcb.com/project/Shika-PedalPCB.pdf
```

Anything else (like part-type headers, such as `Resistor`) can be included on their own row. In the worst case they just will be unparseable and noted as such.

## What are the outputs?

Running the script will output 3 files:

* `Totals`: A list of the total components, in the format `<Component type>|<Component specification>|<Count>`. This file will also output the total count of components which had an unsupported format and which could not be interpreted. Check this carefully to avoid missing parts.
* `Parts`: A structured list that corresponds to each original input row. The program will attempt to add delimiters to improve the structure of this output.
* `Projects`: A list of each individual project, can be used as a handy reference.

### What do I do with them?

You can just keep the files or look at the totals, but they are designed to be pasted into a spreadsheet, such as Google Sheets. Create a new sheet, copy the content of the file you want in a spreadsheet, and paste it into the new sheet. A small popup will appear, and you should select `Paste formatting` -> `Split text to columns` -> `Separator: custom` -> `Type "|"`. You will now have your data in a spreadsheet with columns you can easily tabulate, etc. The `pcb-bom` allows you to choose a column delimiter with the `separator` command-line argument. The default is the pipe character (`|`), since it is rarely used (unlike commas, spaces, or semicolons).