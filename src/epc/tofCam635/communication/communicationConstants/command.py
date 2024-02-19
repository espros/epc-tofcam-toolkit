"""
* Copyright (C) 2019 Espros Photonics Corporation
*
"""

class Command():
    START_MARK = 0xF5     # Start marker for commands
    INDEX_COMMAND = 1     # Index where the command is found in the buffer
    INDEX_DATA = 2        # Index where the data if ound in a command
    INDEX_CHECKSUM = 10   # Index where the checksum is found in a command
    SIZE_TOTAL = 14       # Number of bytes for one command
    SIZE_PAYLOAD = 8      # Number of bytes of the payload of a command
