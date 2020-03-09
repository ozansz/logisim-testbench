import re
import os
import sys
import json
import argparse

from console import Console

DEBUG = False
SAVE_FILE = "test_vectors.txt"

binarize = lambda n: 0 if n <= 0 else 1
positive = lambda n: -n if n < 0 else n

class Bit(object):
    def __init__(self, name, value=0, call_code=None):
        self.name = name
        self.value = value
        self.__call_code = "self.value"

        if call_code is not None:
            self.__call_code = call_code

    @property
    def call_code(self):
        return self.__call_code

    def update(self, value):
        self.value = value

    def __or__(self, other):
        if type(other) == type(self):
            terminal.debug("_OR_:", type(self), self.name, self.value, type(other), other.name, other.value)
            return int(str(self.value) + str(other.value), 2)
        else:
            raise RuntimeError(f"Unsupported OR with: {type(other)}")

    def __ror__(self, other):
        return self.__or__(other)

    def __int__(self):
        return self.value

    def __call__(self):
        terminal.debug(f"EVAL ({self.name}):", self.__call_code)
        ret = eval(self.__call_code)
        terminal.debug(f"EVAL ({self.name}) OK. ({ret})")
        return ret

class LazyVariable(object):
    def __init__(self, name, call_code):
        self.name = name
        self.__call_code = call_code

    def __call__(self):
        terminal.debug(f"EVAL ({self.name}):", self.__call_code)
        ret = eval(self.__call_code)
        terminal.debug(f"EVAL ({self.name}) OK. ({ret})")
        return ret

    @property
    def call_code(self):
        return self.__call_code

def debug_symtab(symtab):
    terminal.debug("====================[ DEBUG ]====================")
    
    for sym in symtab:
        if isinstance(symtab[sym], Bit):
            terminal.debug(f"{symtab[sym].name}: {symtab[sym].value}, {symtab[sym].call_code}")
        if isinstance(symtab[sym], LazyVariable):
            terminal.debug(f"{symtab[sym].name}: {symtab[sym].call_code}")

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
        symtab[sym] = Bit(sym)

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
        symtab[sym] = Bit(sym, call_code=eval_code)

        terminal.debug(f"Output({sym}): {eval_code}")

    terminal.info("Generating truth table...")

    test_vector_lines = list()

    test_vector_lines.append(" ".join(test_config["inputs"] + list(test_config["outputs"].keys())))
    test_vector_lines[0] += "\n"

    terminal.debug("Generating truth table for bits:", test_vector_lines)

    num_inputs = len(test_config["inputs"])

    for seq in [bin(i)[2:].zfill(num_inputs) for i in range(2**num_inputs)]:
        for i in range(num_inputs):
            symtab[test_config["inputs"][i]].update(int(seq[i]))

        try:
            terminal.debug(f"Eval i ({sym}):", symtab[sym].call_code)
            line = [str(symtab[sym]()) for sym in test_config["inputs"]]
        except Exception as e:
            print("ERR (inputs):", e)
            debug_symtab(symtab)
            exit(1)

        try:
            terminal.debug(f"Eval o ({sym}):", symtab[sym].call_code)
            line += [str(symtab[sym]()) for sym in test_config["outputs"]]
        except Exception as e:
            print("ERR (outputs):", e)
            debug_symtab(symtab)
            exit(1)

        terminal.debug(line)
        terminal.debug("\n\n")
        test_vector_lines.append(" ".join(line) + "\n")

    terminal.info("Saving test vectors to:", args.output)

    with open(args.output, "w") as fp:
        fp.writelines(test_vector_lines)

    terminal.info("Done. Goodbye :)")