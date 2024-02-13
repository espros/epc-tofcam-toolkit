"""
* Copyright (C) 2019 Espros Photonics Corporation
*
"""

class Data():
  START_MARK = 0xFA                  # Start marker for data
  INDEX_TYPE = 1                     # Index where the type is found in the buffer
  INDEX_LENGTH = 2                   # Index where the length is found in the buffer
  INDEX_DATA = 4                     # Index where the data is found in the buffer
  SIZE_HEADER = 4                    # Number of bytes for the data header
  SIZE_OVERHEAD = SIZE_HEADER + 4    # Number of overhead bytes = additional bytes to payload
  SIZE_LENGTH = 2                    # Number of bytes for the length