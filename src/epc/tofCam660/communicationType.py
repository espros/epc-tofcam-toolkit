"""
* Copyright (C) 2025 Espros Photonics Corporation
*
"""

class communicationType():
  class Item:
    def __init__(self, id, bytes_per_pixel, name):
      self.id = id
      self.bytes_per_pixel = bytes_per_pixel
      self.name = name
  
  items_by_id = {}
  items_by_name = {}
  
  def __init__(self):
    for item in [ self.Item(0x00, 4, "DATA_DISTANCE_AMPLITUDE"),
                  self.Item(0x01, 2, "DATA_DISTANCE"),
                  self.Item(0x02, 2, "DATA_AMPLITUDE"),
                  self.Item(0x03, 2, "DATA_GRAYSCALE"),
                  self.Item(0x04, 8, "DATA_DCS"),
                ]:
      self.items_by_id[item.id] = item
      self.items_by_name[item.name] = item

  def get_item_by_id(self, id: int):
    return self.items_by_id.get(id)

  def get_item_by_name(self, name: str):
    return self.items_by_name.get(name)