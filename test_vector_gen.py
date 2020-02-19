import re
import os
import sys
import json
import argparse

from console import Console

DEBUG = False
SAVE_FILE = "test_vectors.txt"

binarize = lambda n: 0 if n <= 0 else 1

class Bit(object):
    def __init__(self, value=0, call_code=None):
        self.value = value
        self.__call_code = "self.value"

        if call_code is not None:
            self.__call_code = call_code

    def update(self, value):
        self.value = value

    def __or__(self, other):
        return int(str(self.value) + str(other.value), 2)

    def __ror__(self, other):
        return self.__or__(other)

    def __int__(self):
        return self.value

    def __call__(self):
        return eval(self.__call_code)

class LazyVariable(object):
    def __init__(self, name, call_code):
        self.name = name
        self.__call_code = call_code

    def __call__(self):
        return eval(self.__call_code)

testgen_parser = argparse.ArgumentParser(
    description="Logisim test vector generator script for Sazak's CENG232 TestBench",
    epilog="Made with ❤️ by Ozan Sazak. ### Happy coding :)")

testgen_parser.add_argument("config_file", type=str,
    help="Path of test configuration file")
testgen_parser.add_argument("-o", "--output", default=SAVE_FILE,
    type=str, help="Save the test vector to a custom path")
testgen_parser.add_argument("-v", "--verbose", action="store_true",
    help="Show debug messages (Increase verbosity)")

if __name__ == "__main__":
    args = testgen_parser.parse_args()

    if args.verbose:
        DEBUG = True

    terminal= Console(debug=DEBUG)

    terminal.info("Sazak's CENG232 Logisim TestBench / Test Vector Generator")
    terminal.info(testgen_parser.epilog, "\n")

    if not os.access(args.config_file, os.R_OK):
        terminal.error(f"Config file '{args.config_file}' is not reachable.")
        sys.exit(1)

    with open(args.config_file, "r") as fp:
        test_config = json.load(fp)

    terminal.info("Generating symbol table for test configuration description...")

    symtab = dict()

    for sym in test_config["inputs"]:
        symtab[sym] = Bit()

        terminal.debug(f"Input({sym})")

    for sym in test_config["variables"]:
        eval_code = test_config["variables"][sym]

        for inp_sym in test_config["inputs"]:
            eval_code = re.sub(
                #r"(^" + inp_sym + r"\s+|\s+" + inp_sym + r"$|\s+" + inp_sym + r"\s+)",
                r"\$" + inp_sym,
                f" symtab[\"{inp_sym}\"] ",
                eval_code
            )

        symtab[sym] = LazyVariable(sym, eval_code)

        terminal.debug(f"Var({sym}): {eval_code}")

    for sym in test_config["outputs"]:
        eval_code = test_config["outputs"][sym]

        for var_sym in test_config["variables"]:
            eval_code = re.sub(
                #r"(^" + var_sym + r"\s+|\s+" + var_sym + r"$|\s+" + var_sym + r"\s+)",
                r"\$" + var_sym,
                f" symtab[\"{var_sym}\"]() ",
                eval_code
            )

        eval_code = "binarize(int(" + eval_code + "))"
        symtab[sym] = Bit(call_code=eval_code)

        terminal.debug(f"Output({sym}): {eval_code}")

    terminal.info("Generating truth table...")

    test_vector_lines = list()

    test_vector_lines.append(" ".join(test_config["inputs"] + list(test_config["outputs"].keys())))
    test_vector_lines[0] += "\n"

    terminal.debug("Generating truth table for bits:", test_vector_lines)

    num_inputs = len(test_config["inputs"])

    for seq in [bin(i).replace("0b", "").zfill(num_inputs) for i in range(2**num_inputs)]:
        for i in range(num_inputs):
            symtab[test_config["inputs"][i]].update(int(seq[i]))

        line = [str(symtab[sym]()) for sym in test_config["inputs"]]
        line += [str(symtab[sym]()) for sym in test_config["outputs"]]

        test_vector_lines.append(" ".join(line) + "\n")

    terminal.info("Saving test vectors to:", args.output)

    with open(args.output, "w") as fp:
        fp.writelines(test_vector_lines)

    terminal.info("Done. Goodbye :)")