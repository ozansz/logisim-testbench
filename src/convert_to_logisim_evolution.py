import os
import sys

from string import Template
import xml.etree.ElementTree as ET

def show_usage():
    print(f"[i] Usage: {sys.argv[0]} <circ file>")

TEMPLATE_PATH = "blank.circ"

if __name__ == "__main__":
    if len(sys.argv) != 2:
        show_usage()
        sys.exit()

    source_file = sys.argv[1]
    source_root = ET.parse(source_file)
    circ_block = ET.tostring(source_root.find("circuit")).decode()

    with open(TEMPLATE_PATH, "r") as tfp:
        converted_code = Template(tfp.read()).substitute(
            circ_block=circ_block
        )

    with open(source_file + ".conv.circ", "w") as fp:
        fp.write(converted_code)