import re
import sys
import json

DEBUG = False
SAVE_FILE = "test_vectors.txt"

binarize = lambda n: 0 if n <= 0 else 1

def debug(*args, **kwargs):
    if DEBUG:
        print("[>>] ", *args, **kwargs)

def show_usage():
    print(f"[i] Usage: {sys.argv[0]} <config-file>")

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

if __name__ == "__main__":
    if len(sys.argv) != 2:
        show_usage()
        sys.exit()

    with open(sys.argv[1], "r") as fp:
        test_config = json.load(fp)

    symtab = dict()

    for sym in test_config["inputs"]:
        symtab[sym] = Bit()

        debug(f"Input({sym})")

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

        debug(f"Var({sym}): {eval_code}")

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

        debug(f"Output({sym}): {eval_code}")

    test_vector_lines = list()

    test_vector_lines.append(" ".join(test_config["inputs"] + list(test_config["outputs"].keys())))
    test_vector_lines[0] += "\n"

    debug("Generating truth table for bits:", test_vector_lines)

    num_inputs = len(test_config["inputs"])

    for seq in [bin(i).replace("0b", "").zfill(num_inputs) for i in range(2**num_inputs)]:
        for i in range(num_inputs):
            symtab[test_config["inputs"][i]].update(int(seq[i]))

        line = [str(symtab[sym]()) for sym in test_config["inputs"]]
        line += [str(symtab[sym]()) for sym in test_config["outputs"]]

        test_vector_lines.append(" ".join(line) + "\n")

    debug("Saving test vectors to:", SAVE_FILE)

    with open(SAVE_FILE, "w") as fp:
        fp.writelines(test_vector_lines)