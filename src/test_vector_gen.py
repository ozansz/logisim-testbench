import re
import os
import sys
import json
import argparse

from .console import Console

DEBUG = False
SAVE_FILE = "test_vectors.txt"

ALL_CHPIS = [
    'Base:Text',
    'Base:Splitter',
    'Base:Clock',
    'Base:Pin',
    'Base:Probe',
    'CENG232 Gates:AND Gate',
    'CENG232 Gates:OR Gate',
    'CENG232 Gates:NOT Gate',
    'CENG232 Gates:NOR Gate',
    'CENG232 Gates:Constant',
    'CENG232 Gates:Controlled Buffer',
    'CENG232 Gates:Buffer',
    'CENG232 Gates:Controlled Inverter',
    'CENG232 Gates:XOR Gate',
    'CENG232 Gates:NAND Gate',
    'CENG232 Gates:XNOR Gate',
    'CENG232 ICs:4-bit Latch (7475)',
    'CENG232 ICs:4 bit full adder (7483)',
    'CENG232 ICs:Dual J-K Flip Flop (74112)',
    'CENG232 ICs:Dual D Flip Flop (7474)',
    'CENG232 ICs:3-to-8 decoder (74138)',
    'CENG232 ICs:4-to-1 MUX (x2) (74153)',
    'CENG232 ICs:4-bit shift register (74195)',
    'CENG232 ICs:2-to-4 Decoder (x2) (74155)',
    'CENG232 ICs:4-bit shift register (7495)'
]

binarize = lambda n: 0 if n <= 0 else 1
positive = lambda n: -n if n < 0 else n

debug_terminal = Console(debug=DEBUG)

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
            debug_terminal.debug("_OR_:", type(self), self.name, self.value, type(other), other.name, other.value)
            return int(str(self.value) + str(other.value), 2)
        else:
            raise RuntimeError(f"Unsupported OR with: {type(other)}")

    def __ror__(self, other):
        return self.__or__(other)

    def __int__(self):
        return self.value

    def __call__(self):
        debug_terminal.debug(f"EVAL ({self.name}):", self.__call_code)
        ret = eval(self.__call_code)
        debug_terminal.debug(f"EVAL ({self.name}) OK. ({ret})")
        return ret

class LazyVariable(object):
    def __init__(self, name, call_code):
        self.name = name
        self.__call_code = call_code

    def __call__(self):
        debug_terminal.debug(f"EVAL ({self.name}):", self.__call_code)
        ret = eval(self.__call_code)
        debug_terminal.debug(f"EVAL ({self.name}) OK. ({ret})")
        return ret

    @property
    def call_code(self):
        return self.__call_code

def debug_symtab(symtab):
    debug_terminal.debug("====================[ DEBUG ]====================")
    
    for sym in symtab:
        if isinstance(symtab[sym], Bit):
            debug_terminal.debug(f"{symtab[sym].name}: {symtab[sym].value}, {symtab[sym].call_code}")
        if isinstance(symtab[sym], LazyVariable):
            debug_terminal.debug(f"{symtab[sym].name}: {symtab[sym].call_code}")

class SimulationProperties(object):
    def __init__(self, inputs, outputs):
        self.allowed_chips = []
        self.inputs = inputs
        self.outputs = outputs
        self.runs = []

    def allow_chip(self, chip):
        if chip not in self.allowed_chips:
            self.allowed_chips.append(chip)

    def disallow_chip(self, chip):
        if chip in self.allowed_chips:
            self.allowed_chips.remove(chip)

    def add_run(self, inputs, outputs):
        self.runs.append((inputs, outputs))

    def save_to(self, file_path):
        with open(file_path, "w") as fp:
            fp.write("allowed_chips= \\\n\tBase:Pin")

            for chip in self.allowed_chips:
                fp.write(f", \\\n\t{chip}")

            fp.write(f"\n\ninputs={','.join(self.inputs)}")
            fp.write(f"\noutputs={','.join(self.outputs)}\n")
            fp.write(f"\nnumber_of_runs={len(self.runs)}\n")

            for i in range(1, len(self.runs) + 1):
                fp.write(f"\nrun.{i}.length = 1")

            fp.write("\n")

            for index, run in enumerate(self.runs):
                fp.write(f"\nrun.{index + 1}.state.1 = {','.join(run[0])};{','.join(run[1])}")
            
            fp.write("\n")

symtab = dict()

def generate_test_vector(config_file, output_file=SAVE_FILE, verbose=False):
    global symtab
    
    terminal = Console(debug=verbose)

    terminal.info("Sazak's CENG232 Logisim TestBench / Test Vector Generator")
    terminal.info("Made with ❤️ by Ozan Sazak. ### Happy coding :)\n")

    if not os.access(config_file, os.R_OK):
        terminal.error(f"Config file '{config_file}' is not reachable.")
        sys.exit(1)

    with open(config_file, "r") as fp:
        test_config = json.load(fp)

    terminal.info("Generating symbol table for test configuration description...")

    symtab = dict()

    props = SimulationProperties(test_config["inputs"][:], list(test_config["outputs"].keys()))

    if "$meta" in test_config:
        if "allowed_chips" in test_config["$meta"]:
            ac = test_config["$meta"]["allowed_chips"]

            if type(ac) == list:
                for chip in ac:
                    props.allow_chip(chip)
            elif ac == '__all__':
                props.allowed_chips = ALL_CHPIS[:]
            else:
                print("!! Unsupported 'allowed_chips':", test_config["$meta"]["allowed_chips"])
                exit(1)
        else:
            props.allowed_chips = ALL_CHPIS[:]
    else:
        props.allowed_chips = ALL_CHPIS[:]

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
            _inputs = [str(symtab[sym]()) for sym in test_config["inputs"]]
            line = _inputs[:]
        except Exception as e:
            print("ERR (inputs):", e)
            debug_symtab(symtab)
            exit(1)

        try:
            terminal.debug(f"Eval o ({sym}):", symtab[sym].call_code)
            _outputs = [str(symtab[sym]()) for sym in test_config["outputs"]]
            line += _outputs
        except Exception as e:
            print("ERR (outputs):", e)
            debug_symtab(symtab)
            exit(1)

        props.add_run(_inputs, _outputs)

        terminal.debug(line)
        terminal.debug("\n\n")
        test_vector_lines.append(" ".join(line) + "\n")

    terminal.info("Saving test vectors to:", output_file)

    props.save_to(output_file + ".properties")

    with open(output_file, "w") as fp:
        fp.writelines(test_vector_lines)

    terminal.info("Done. Goodbye :)")