class Console(object):
    """ Console class
    Colored terminal output functions
    """

    COLOR_RED = "\u001b[31;1m"
    COLOR_BLUE = "\u001b[34;1m"
    COLOR_RESET = "\u001b[0m"

    def __init__(self, debug=False):
        self._debug = debug

    def debug(self, *args, **kwargs):
        if self._debug:
            print(" [DBG] ", *args, **kwargs)

    @staticmethod
    def error(*args, **kwargs):
        print(Console.COLOR_RED, "[!!!] Error:", Console.COLOR_RESET, *args, **kwargs)

    @staticmethod
    def info(*args, **kwargs):
        print(Console.COLOR_BLUE, "[[i]]", Console.COLOR_RESET, *args, **kwargs)