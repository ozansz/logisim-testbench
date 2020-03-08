#!/bin/bash
set -e

test_vectors_file="test_vectors.txt"
debug_switch=false

show_usage() {
    echo -e "\n[i] Usage: $(basename $0) <circ-file> <test-configuration> [-v]"
    echo -e "                circ-file          : Logisim .circ circuit file to be tested"
    echo -e "                test-configuration : Test configuration definitions file"
    echo -e "                -v                 : Show debug messages, improved verbosity\n"
}

# Check for the right number of command-line arguments
if [ "$#" -lt 2 ]; then
    show_usage
    exit
fi

if [ "$#" -gt 3 ]; then
    show_usage
    exit
fi

# Set debug switch if verbose option is given
if [ "$#" -eq 3 ]; then
    if [ "$3" == "-v" ]; then
        debug_switch=true
    else
        show_usage
        exit
    fi
fi

# Convert the .circ file to Logisim Evolution format
python3 convert_to_logisim_evolution.py "$1"

# Generate test vectors
if [ "$debug_switch" = true ]; then
    python3 test_vector_gen.py -v "$2"
else
    python3 test_vector_gen.py "$2"
fi

# Run the testbench
java -jar logisim-evolution.jar "$1.conv.circ" -test main "$test_vectors_file"

# Clean temporary files
rm -f "$1.conv.circ"
#rm -f "$test_vectors_file"