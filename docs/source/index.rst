.. EPC TOFcam python package documentation master file, created by
   sphinx-quickstart on Tue Feb 13 08:30:57 2024.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

ESPROS TOFcam Toolkit
=====================================================
| Website: https://www.espros.com/
| Products: https://www.digikey.com/en/supplier-centers/espros  
| Source: https://github.com/espros/epc-tofcam-toolkit

Introduction
------------
| This package provides a python interface to the ESPROS TOFcam's.
| It also provides a simple GUI to visualize the data from the camera.


.. image:: images/gui660_pointcloud.png
   :alt: GUI-TOFcam660
   :align: center


Compatibility
-------------
| This package is compatible with python 3.10 and above.
| Currently supported camera modules are:  

* `TOFcam660 - purchase on digikey <https://www.digikey.com/en/products/filter/optical-sensors/camera-modules/1003?s=N4IgTCBcDaICoHsBmBjAhgWwAQDYcAYQBdAXyA>`_ 
* `TOFcam635 - purchase on digikey <https://www.digikey.com/en/product-highlight/e/espros/tof-cam-635-miniaturized-3d-camera>`_
* `TOFcam611 - purchase on digikey <https://www.digikey.com/en/products/detail/espros-photonics-ag/TOF-FRAME-611/10516851>`_
* `TOFrange611 - purchase on digikey <https://www.digikey.com/en/products/detail/espros-photonics-ag/TOF-RANGE-611/10516871>`_

Datasheets
----------
| Additional information about the camera modules can be found in the datasheets:
| https://www.espros.com/downloads/02_Cameras_and_Modules/

.. toctree::
   :maxdepth: 2
   :caption: Contents:
   
   install_instructions.md
   gui_instructions.md
   tofCam_modules.rst
   api.rst

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
