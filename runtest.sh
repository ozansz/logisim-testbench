#!/bin/bash
set -e

test_vectors_file="test_vectors.txt"

show_usage() {
    echo -e "\n[i] Usage: $(basename $0) <circ-file> <test-configuration>\n"
}

# Check for the right number of command-line arguments
if [ "$#" -ne 2 ]; then
    show_usage
    exit
fi

# Convert the .circ file to Logisim Evolution format
python3 convert_to_logisim_evolution.py "$1"

# Generate test vectors
python3 test_vector_gen.py "$2"

# Run the testbench
java -jar logisim-evolution.jar "$1.conv.circ" -test main "$test_vectors_file"

# Clean temporary files
rm -f "$1.conv.circ"
#rm -f "$test_vectors_file"