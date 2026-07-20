
import sys
import getopt
import qdarktheme
from pyqtgraph.Qt import QtCore, QtWidgets
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication
from epc.hawkeyeBt.hawkeyeBt import HawkeyeBt
from epc.tofCam_gui import Base_TOFcam_Bridge
from epc.tofCam_gui.gui_hawkeye import GUI_Hawkeye

class BleScannerWorker(QtCore.QObject):
    finished = QtCore.Signal(list)

    def __init__(self, bt_dev):
        super().__init__()
        self.bt_dev = bt_dev

    def run(self):
        devices = self.bt_dev.scan_for_devices_dict()
        self.finished.emit(devices)


class BleDeviceSelectionDialog(QtWidgets.QDialog):
    def __init__(self, bt_dev):
        super().__init__()
        self.bt_dev = bt_dev
        self.selected_mac = None

        self.setWindowTitle("Select Bluetooth Device")
        self.setMinimumSize(400, 500)

        layout = QtWidgets.QVBoxLayout(self)

        self.status_label = QtWidgets.QLabel("Searching for devices...")
        layout.addWidget(self.status_label)

        self.list_widget = QtWidgets.QListWidget()
        layout.addWidget(self.list_widget)

        self.progress = QtWidgets.QProgressBar()
        self.progress.setRange(0, 0)
        layout.addWidget(self.progress)

        btn_layout = QtWidgets.QHBoxLayout()
        self.rescan_btn = QtWidgets.QPushButton("Rescan")
        self.rescan_btn.clicked.connect(self.start_scan)
        self.rescan_btn.setEnabled(False)

        self.connect_btn = QtWidgets.QPushButton("Connect")
        self.connect_btn.clicked.connect(self.accept)
        self.connect_btn.setEnabled(False)

        btn_layout.addWidget(self.rescan_btn)
        btn_layout.addWidget(self.connect_btn)
        layout.addLayout(btn_layout)

        self.list_widget.itemSelectionChanged.connect(self._on_selection_changed)
        QtCore.QTimer.singleShot(100, self.start_scan)

    def _on_selection_changed(self):
        self.connect_btn.setEnabled(self.list_widget.currentRow() >= 0)
        item = self.list_widget.currentItem()
        if item:
            self.selected_mac = item.data(QtCore.Qt.UserRole)

    def start_scan(self):
        self.rescan_btn.setEnabled(False)
        self.connect_btn.setEnabled(False)
        self.list_widget.clear()
        self.progress.show()
        self.status_label.setText("Scanning for devices...")

        self.scan_thread = QtCore.QThread()
        self.scan_thread.setObjectName("ble device scan thread")
        self.worker = BleScannerWorker(self.bt_dev)
        self.worker.moveToThread(self.scan_thread)
        self.scan_thread.started.connect(self.worker.run)
        self.worker.finished.connect(self._on_scan_finished)
        self.worker.finished.connect(self.scan_thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.scan_thread.finished.connect(self.scan_thread.deleteLater)
        self.scan_thread.start()

    def _on_scan_finished(self, devices):
        self.progress.hide()
        self.rescan_btn.setEnabled(True)
        self.status_label.setText(f"Found {len(devices)} devices:")

        for dev in devices:
            name = dev.get('name', 'Unknown')
            addr = dev['address']
            rssi = dev['rssi']
            display_text = f"<b>{name}</b><br/>{addr} | RSSI: {rssi} dBm"

            item = QtWidgets.QListWidgetItem()
            label = QtWidgets.QLabel(display_text)
            item.setSizeHint(label.sizeHint())
            item.setData(QtCore.Qt.UserRole, addr)
            self.list_widget.addItem(item)
            self.list_widget.setItemWidget(item, label)


class Hawkeye_bridge(Base_TOFcam_Bridge):
    C = 299792458 # m/s
    MAX_AMPLITUDE = 2896
    MAX_GRAYSCALE = 2**10
    def __init__(self, gui: GUI_Hawkeye, cam: HawkeyeBt):
        super(Hawkeye_bridge, self).__init__(cam, gui)
        self.cam: HawkeyeBt
        self._get_image_cb = self.cam.get_distance_image
        self.__distance_unambiguity = 7.5 # m 

        # even though start_stream & stop_stream have a bool as return, always return None to the callbacks:
        self.streamer.start_stream_cb = lambda: (cam.bt_cam.start_stream(), None)[1]
        self.streamer.post_stop_cb = lambda: (cam.bt_cam.stop_stream(), None)[1]

        gui.imageTypeWidget.signal_value_changed.connect(self._set_image_type)
        gui.modulationFrequency.signal_value_changed.connect(lambda: self._set_modulation_settings())
        gui.integrationTimes.signal_value_changed.connect(self._set_integration_times)
        gui.minAmplitude.signal_value_changed.connect(lambda minAmp: self._set_min_amplitude(minAmp))
        gui.medianFilter.signal_filter_changed.connect(lambda: self._set_filter_settings())
        gui.averageFilter.signal_filter_changed.connect(lambda: self._set_filter_settings())
        gui.edgeFilter.signal_filter_changed.connect(lambda: self._set_filter_settings())
        gui.temporalFilter.signal_filter_changed.connect(lambda: self._set_filter_settings())
        gui.roiSettings.signal_roi_changed.connect(self._set_roi)
        
        self.gui.setDefaultValues()

    def _set_min_amplitude(self, minAmp: int):
        self.cam.settings.set_minimal_amplitude(minAmp)
        self.capture()

    def _set_integration_times(self, type: str, value: int):
        tof = self.gui.integrationTimes.getTimeAtIndex(0)
        self.cam.settings.set_integration_time(tof)
        self.capture()

    def _set_modulation_settings(self):
        frequency = float(self.gui.modulationFrequency.getSelection().split(' ')[0])
        self.__distance_unambiguity = self.C / (2 * frequency * 1e6)

        self.gui.imageView.setLevels(0, self.__distance_unambiguity*1000)
        self.cam.settings.set_modulation(frequency)
        self.capture()

    def _set_image_type(self, image_type: str):
        if image_type == 'Distance':
            self.gui.imageView.setActiveView('image')
            self._get_image_cb = self.cam.get_distance_image
            self.gui.imageView.setColorMap(self.gui.imageView.DISTANCE_CMAP)
            self.gui.imageView.setLevels(0, self.__distance_unambiguity*1000)
        elif image_type == 'Amplitude':
            self.gui.imageView.setActiveView('image')
            self._get_image_cb = self.cam.get_amplitude_image
            self.gui.imageView.setColorMap(self.gui.imageView.DISTANCE_CMAP)
            # keep the min just below zero to have values=0 not shown black, but dark blue:
            self.gui.imageView.setLevels(-0.1, self.MAX_AMPLITUDE)
        elif image_type == 'Grayscale':
            self.gui.imageView.setActiveView('image')
            self._get_image_cb = self.cam.get_grayscale_image
            self.gui.imageView.setColorMap(self.gui.imageView.GRAYSCALE_CMAP)
            self.gui.imageView.setLevels(0, self.MAX_GRAYSCALE)
        self.capture()

    def _set_filter_settings(self):
        if not isinstance(self.cam, HawkeyeBt):
            return
        self.cam.medianFilterOn = self.gui.medianFilter.isChecked()
        self.cam.averageFilterOn = self.gui.averageFilter.isChecked()
        self.cam.edgeFilterOn = self.gui.edgeFilter.isChecked()
        self.cam.edgeFilterThreshold = self.gui.edgeFilter.threshold.value()
        self.cam.temporalFilterOn = self.gui.temporalFilter.isChecked()
        self.cam.temporalFilter.alpha = self.gui.temporalFilter.factor.value()
        self.cam.temporalFilter.threshold = self.gui.temporalFilter.threshold.value()

    def _set_roi(self, x1: int, y1: int, x2: int, y2: int):
        self.cam.settings.set_roi((x1, y1, x2, y2))
        try:
            self.getImage()  # trow away next image since it has wrong roi
        except:
            pass
    
    def capture(self, mode=0):
        try:
            camera = self.cam.bt_cam
        except AttributeError:
            camera = None
        if camera and not self.streamer.is_streaming():
            camera.single_capture()
        super().capture()


def get_mac_address(cam: HawkeyeBt):
    mac_address = None
    try:
        opts, args = getopt.getopt(sys.argv[1:], "m:", ["mac="])
        for opt, arg in opts:
            if opt in ('-m', '--mac'):
                mac_address = arg
    except:
        print('Argument parsing failed')
    if mac_address == None:
        print(f'No mac-address specified. Searching for devices now')
        selector = BleDeviceSelectionDialog(cam.bt_cam.bt_dev)
        result = selector.exec()
        if result == QtWidgets.QDialog.Accepted and selector.selected_mac is not None:
            mac_address = selector.selected_mac
    return mac_address

def main():
    with HawkeyeBt("00:00:00:00:00:00") as ble_cam:
        app = QApplication([])

        mac = get_mac_address(ble_cam)
        if mac is None:
            ble_cam.bt_cam.bt_dev.disconnect()
            sys.exit(0)
        ble_cam.bt_cam.mac_addr = mac
        ble_cam.bt_cam.connect()
        ble_cam.initialize()
        ble_cam.settings.get_roi()

        qdarktheme.setup_theme('auto', default_theme='dark')
        gui = GUI_Hawkeye()
        bridge = Hawkeye_bridge(gui, ble_cam)
        QTimer.singleShot(100, gui.toolBar.playButton.trigger)
        gui.show()
        app.exec()

if __name__ == '__main__':
    main()
