import sys

import qdarktheme
from PySide6 import QtWidgets

from epc.tofCam_gui import Base_GUI_TOFcam
from epc.tofCam_gui.widgets import (DropDownSetting, GroupBoxSelection,
                                    IntegrationTimes, RoiSettings,
                                    SettingsGroup, SpinBoxSetting,
                                    VideoWidget, FloatInput, SliderSetting)
from epc.tofCam_gui.widgets.filter_widgets import (EdgeFilter,
                                                   InterferenceFilter,
                                                   SimpleFilter,
                                                   TemporalFilter,
                                                   KalmanFilter)


class ROISettings670(RoiSettings):
    def __init__(self, width, height):
        super(ROISettings670, self).__init__(width, height)

    def roiChanged(self):
        """ Overwrite the roiChanged method to update the y2 value when y1 is changed and vice versa """
        sender = self.sender()
        if sender == self.y1:
            self.y2.setValue(self.roi_height - self.y1.value())
        elif sender == self.y2:
            self.y1.setValue(self.roi_height - self.y2.value())
        super().roiChanged()


class GUI_TOFcam670(Base_GUI_TOFcam):
    def __init__(self, title='GUI-TOFcam-670', parent=None):
        super(GUI_TOFcam670, self).__init__(title)

        # Create the video widget
        self.imageTypeWidget = GroupBoxSelection('Image Type', ['Distance', 'Amplitude', 'Grayscale', 'DCS', 'Point Cloud'])
        self.hdrModeDropDown = DropDownSetting('HDR Mode', ['HDR Off', 'HDR Temporal'], default='HDR Temporal')
        self.modulationFrequency = SpinBoxSetting('Modulation Frequency (MHz)', 1, 24, default=20)
        self.modeSettings = SettingsGroup('Camera Modes', [self.modulationFrequency, self.hdrModeDropDown])
        self.lensType = DropDownSetting('Lens Type', ['Narrow Field', 'Standard Field', 'Wide Field', 'Wide Wide Field', 'Ultra Wide Field'], default='Wide Field')
        self.pointCloudSettings = SettingsGroup('Point Cloud Settings', [self.lensType])
        self.pointCloudSettings.setEnabled(False)
        self.integrationTimes = IntegrationTimes(['Low', 'Mid', 'High', 'Grayscale'], [40, 400, 4000, 400], [4000, 4000, 4000, 4000])
        self.integrationTimes.autoMode.setVisible(False)
        self.minAmplitude = SliderSetting('Minimal Amplitude (LSB)', 0, 300, default=100)

        # Filters        
        self.medianFilter = SimpleFilter('Median Filter')
        self.averageFilter = SimpleFilter('Average Filter')
        self.edgeFilter = EdgeFilter(range=(0, 5000), threshold=150)
        self.temporalFilter = TemporalFilter()
        self.kalmanFilter = KalmanFilter('Kalman Filter')
        self.interferenceFilter = InterferenceFilter(limit=300)
        self.builtInFilter = SettingsGroup('Image Filters', [self.medianFilter, self.averageFilter, self.edgeFilter, self.temporalFilter, self.kalmanFilter, self.interferenceFilter])

        # Tool Tips
        withLimit = '<div style="max-width: 200px;">'
        self.imageTypeWidget.setToolTip(
            withLimit + 'Select the type of image to display. '
            'Point Cloud will show a 3D representation of the scene.</div>')
        self.hdrModeDropDown.comboBox.setToolTip(
            withLimit + 'Select the HDR mode. HDR Temporal will automatically choose '
            'the integration time for each pixel to optimize image quality.</div>')
        self.modulationFrequency.spinBox.setToolTip(
            withLimit + 'Set the modulation frequency of the camera. Higher frequencies '
            'can provide better resolution but lower maximal range.</div>')
        self.lensType.setToolTip(
            withLimit + 'Select the lens type. This will affect the projection of the '
            'point cloud and the field of view of the camera.</div>')
        self.integrationTimes.setToolTip(
            withLimit + 'Set the integration times. Low, Mid, and High correspond to the '
            'different exposure times used in HDR Temporal mode. '
            'Grayscale is used for grayscale images.</div>')
        self.minAmplitude.setToolTip(
            withLimit + 'Set the minimal amplitude threshold. Pixels with an amplitude '
            'below this value will be ignored in the distance calculation.</div>')
        self.medianFilter.checkBox.setToolTip(
            withLimit + 'Apply a median filter to the distance image. '
            'This can help reduce noise and improve image quality.</div>')
        self.averageFilter.checkBox.setToolTip(
            withLimit + 'Apply an average filter to the distance image. '
            'This can help reduce noise but may also blur the image.</div>')
        self.edgeFilter.checkBox.setToolTip(
            withLimit + 'Apply an edge filter to the distance image. '
            'This can reduce floating pixels at sharp edges.</div>')
        self.temporalFilter.checkBox.setToolTip(
            withLimit + 'Apply a temporal filter to the distance image. '
            'This can help reduce noise by averaging over multiple frames.</div>')
        self.kalmanFilter.checkBox.setToolTip(
            withLimit + 'Apply a Kalman filter to the distance image. '
            'This can help reduce noise and improve tracking of moving objects.</div>')
        self.interferenceFilter.checkBox.setToolTip(
            withLimit + 'Apply an interference filter to the distance image. '
            'This can help reduce interference from other light sources and improve image quality.</div>')

        # Create Layout for settings
        self.settingsLayout.addWidget(self.imageTypeWidget)
        self.settingsLayout.addWidget(self.modeSettings)
        self.settingsLayout.addWidget(self.pointCloudSettings)
        self.settingsLayout.addWidget(self.integrationTimes)
        self.settingsLayout.addWidget(self.minAmplitude)
        self.settingsLayout.addWidget(self.builtInFilter)

        self.complete_setup()

    def _set_bridge(self, cam:"TOFcam") -> None:
        from epc.tofCam_gui.gui_tofCam670_bridge import TOFcam670_bridge
        super()._set_bridge(cam=cam, _bridge_type=TOFcam670_bridge)


def main():
    app = QtWidgets.QApplication(sys.argv)

    qdarktheme.setup_theme()
    stream = GUI_TOFcam670()
    stream.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
