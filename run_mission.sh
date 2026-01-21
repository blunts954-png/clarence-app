#!/bin/bash

# Wrapper script to execute the Synapse AI mission

# Get the absolute path of the script's directory to ensure
# engine.py is found, regardless of where this script is called from.
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Mission parameters
URL="https://bakersfield.craigslist.org/search/jjj"
RECIPIENT="blunts954@gmail.com"

echo "Executing Synapse AI mission..."
/usr/bin/python3 "$DIR/engine.py" "$URL" --recipient "$RECIPIENT" --pages 1
echo "Mission complete."
