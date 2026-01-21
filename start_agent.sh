#!/bin/bash

# Synapse AI Autonomous Agent Launcher

# Get the absolute path of the script's directory
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Log file location
LOG_FILE="$DIR/agent.log"
ENV_LOG_FILE="$DIR/agent_env.log"

# --- DEBUG: DUMP ENVIRONMENT ---
echo "--- AGENT ENVIRONMENT SNAPSHOT ---" > $ENV_LOG_FILE
echo "Timestamp: $(date)" >> $ENV_LOG_FILE
echo "Running as user: $(whoami)" >> $ENV_LOG_FILE
echo "Current Directory: $(pwd)" >> $ENV_LOG_FILE
echo "Script Directory: $DIR" >> $ENV_LOG_FILE
echo "
--- ENVIRONMENT VARIABLES ---" >> $ENV_LOG_FILE
printenv >> $ENV_LOG_FILE
echo "------------------------------------" >> $ENV_LOG_FILE

# Mission parameters
URL="https://bakersfield.craigslist.org/search/jjj"
RECIPIENT="blunts954@gmail.com"

echo "-----" >> $LOG_FILE
echo "Agent started at $(date)" >> $LOG_FILE

while true
  do
    echo "[$(date)] Running mission for $URL" >> $LOG_FILE
    /usr/bin/python3 "$DIR/engine.py" "$URL" --recipient "$RECIPIENT" --pages 1 >> $LOG_FILE 2>&1
    if [ $? -eq 0 ]; then
      echo "[$(date)] Mission successful." >> $LOG_FILE
    else
      echo "[$(date)] Mission failed. Check log for errors." >> $LOG_FILE
    fi
    echo "[$(date)] Sleeping for 1 hour." >> $LOG_FILE
    sleep 3600
done
