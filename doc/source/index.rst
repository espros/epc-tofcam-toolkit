.. EPC TOFcam python package documentation master file, created by
   sphinx-quickstart on Tue Feb 13 08:30:57 2024.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

espros TOF Cam Toolkit
=====================================================
Introduction
------------
| This package provides a python interface to the espros TOF cameras.
| It also provides a simple GUI to visualize the data from the camera.

Currently supported camera modules are:  
   * TOFcam-611
   * TOFcam-635
   * TOFcam-660

.. image:: images/gui660_pointcloud.png
   :alt: GUI TOFcam660
   :align: center

Compatibility
-------------
This package is compatible with python 3.10 and above.

.. toctree::
   :maxdepth: 2
   :caption: Contents:
   
   install_instructions.md
   gui_instructions.md
   tofCam_modules.md

.. include:: source/install_instructions.md
.. include:: source/gui_instructions.md
.. include:: source/tofCam_modules.md

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
