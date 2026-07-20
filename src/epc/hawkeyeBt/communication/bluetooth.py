import asyncio
import atexit
import logging
import threading
import time
from abc import ABC
from enum import Enum
from typing import Optional, Type

import numpy as np
from bumble import gatt_client, l2cap
from bumble.core import UUID, AdvertisingData
from bumble.device import Advertisement, Connection, Device, Peer
from bumble.hci import Address
from bumble.transport import open_transport
from bumble.transport.common import Transport

log = logging.getLogger(__name__)


class SecureDataBuffer:
    def __init__(self, marker: bytes = b'\xff\xff\xfe\xfe'):
        self.buffer = bytearray()
        self.condition = threading.Condition()
        self.marker = marker

    def add_data(self, data):
        """Called by the Bumble callback."""
        with self.condition:
            self.buffer.extend(data)
            # Wake up any thread waiting for data
            self.condition.notify_all()

    def wait_and_pop(self, n, timeout=None):
        """Called by your processing thread."""
        with self.condition:
            while True:
                # Wait until we find the marker and have 'n' bytes after it
                def predicate():
                    idx = self.buffer.find(self.marker)
                    return idx != -1 and len(self.buffer) >= idx + len(self.marker) + n

                success = self.condition.wait_for(predicate, timeout=timeout)

                if success:
                    idx = self.buffer.find(self.marker)
                    payload_start = idx + len(self.marker)

                    # Check if another marker is found within the payload
                    next_marker = self.buffer.find(self.marker, payload_start, payload_start + n)
                    if next_marker != -1:
                        del self.buffer[:next_marker]
                        continue

                    data = self.buffer[payload_start:payload_start + n]
                    del self.buffer[:payload_start + n]
                    return data
                return None  # Timeout reached


class ControlPointDataInterface(ABC):
    Uuid: str

    class Commands(Enum):
        GET_CONTROL = 0x01
        SET_CONTROL = 0x02
        # Other commands can exist, but these two must exist

    class SubCommands(Enum):
        # We assume this Enum exists, regardless of its members
        pass


class ControlPointHandler():
    class Responses(Enum):
        SUCCESS = 0x00
        INVALID_OPCODE = 0x01
        INVALID_LENGTH = 0x02
        ERROR = 0x03

    def __init__(self, cam: "BluetoothCam", control_point_data: Type[ControlPointDataInterface]):
        self.Camera = cam
        self.ControlPoint = control_point_data

    def issue_cmd(self, cmd: Enum) -> bool:
        self.Camera._notification_event.clear()
        command = bytes([cmd.value])
        self.Camera.bt_dev.write_gatt_char(self.ControlPoint.Uuid, command)
        if self.Camera._notification_event.wait(timeout=1.0):
            data = self.Camera._notification_data
            if (data and len(data) >= 2 and
                    data[0] == cmd.value and
                    data[1] == self.Responses.SUCCESS.value):
                return True
        return False

    def get_control(self, cmd: Enum, min_data_size: int = 0) -> bytes | None:
        self.Camera._notification_event.clear()
        command = bytes([self.ControlPoint.Commands.GET_CONTROL.value, cmd.value])
        self.Camera.bt_dev.write_gatt_char(self.ControlPoint.Uuid, command)
        if self.Camera._notification_event.wait(timeout=1.0):
            data = self.Camera._notification_data
            if (data and len(data) >= 3 + min_data_size and
                    data[0] == self.ControlPoint.Commands.GET_CONTROL.value and
                    data[1] == self.Responses.SUCCESS.value and
                    data[2] == cmd.value):
                return data[3:]
        return None

    def set_control(self, cmd: Enum, value: bytes) -> bool:
        self.Camera._notification_event.clear()
        command = bytes([self.ControlPoint.Commands.SET_CONTROL.value, cmd.value]) + value
        self.Camera.bt_dev.write_gatt_char(self.ControlPoint.Uuid, command)
        if self.Camera._notification_event.wait(timeout=1.0):
            data = self.Camera._notification_data
            if (data and len(data) >= 2 and
                    data[0] == self.ControlPoint.Commands.SET_CONTROL.value and
                    data[1] == self.Responses.SUCCESS.value):
                return True
        return False


class _CameraControlPointData(ControlPointDataInterface):
    Uuid = '0000FE54-2AC5-4541-9D4C-21EDAE82ED19'

    class Commands(Enum):
        GET_CONTROL = 0x01
        SET_CONTROL = 0x02
        START_STREAM = 0x03
        STOP_STREAM = 0x04
        SINGLE_CAPTURE = 0x05

    class SubCommands(Enum):
        MODE = 0x01
        INTEGRATION_TIME = 0x02
        ROI = 0x03
        MODULATION_FREQUENCY = 0x04
        MIN_AMPLITUDE = 0x05
        COMPENSATION_PHASE_OFFSET = 0x06
        COMPENSATION_PHASE_ERROR = 0x07
        COMPENSATION_TEMPERATURE = 0x08
        COMPENSATION_GRAYSCALE_DSNU = 0x09


class _AquisitionMode(Enum):
    DCS_4 = 0
    GRAYSCALE = 1
    HDR = 2


class BluetoothCam():
    AquisitionMode = _AquisitionMode
    CameraCpData = _CameraControlPointData

    def __init__(self, mac_addr: str, name: str = "peripheral", roi: tuple[int, int, int, int] = (50, 0, 109, 59)):
        """
        mac_addr: Bluetooth MAC address of the camera
        name:     Name of the camera
        roi:      (x1, y1, x2, y2) where as (x1, y1) is the top-left corner ⇱ and (x2, y2) is the bottom-right ⇲ corner.
        """
        self.mac_addr = mac_addr
        self.bt_dev = BluetoothDevice(device_name=name)
        self._roi = roi
        self._image_store = SecureDataBuffer(marker=b'\xff\xff\xfe\xfe')
        self._notification_event = threading.Event()
        self._notification_data = None
        self.camera_controlpoint_handler = ControlPointHandler(self, self.CameraCpData)

    def __enter__(self):
        self.bt_dev.__enter__()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()
        if self.bt_dev:
            self.bt_dev.__exit__(exc_type, exc_val, exc_tb)

    def on_data_received(self, data):
        self._image_store.add_data(data)
        # print(f"L2CAP Data Received: >>>\n  0x{data.hex()}\n<<<")

    def on_notification(self, data):
        """
        Callback function to handle incoming indications.
        """
        # print(data.hex())
        # opCode = data.hex()[0:2]
        # response = data.hex()[2:]
        # print(f"  OpCode   : 0x{opCode}")
        # print(f"  Response  : 0x{response}")
        self._notification_data = data
        self._notification_event.set()

    def send_data(self, path):
        # logging.info(f"Manual Packet: {packet.hex()}")
        # self.bt_dev._peripheral_l2cap_channel.write(packet)
        pass

    def connect(self):
        self.bt_dev.connect(str.upper(self.mac_addr))
        time.sleep(2)
        specs = l2cap.LeCreditBasedChannelSpec(
            psm=0x0025,
            mtu=2000,
            mps=2000,
            max_credits=255,
        )
        self.bt_dev.register_notification(char_uuid=self.CameraCpData.Uuid, callback=self.on_notification)
        self.bt_dev.open_data_channel(callback=self.on_data_received, specs=specs)

    def disconnect(self):
        if self.bt_dev and self.bt_dev.is_connected():
            self.bt_dev.unregister_notification(char_uuid=self.CameraCpData.Uuid)
            self.bt_dev.disconnect()

    def start_stream(self) -> bool:
        logging.info("Starting stream...")
        return self.camera_controlpoint_handler.issue_cmd(self.CameraCpData.Commands.START_STREAM)

    def stop_stream(self) -> bool:
        logging.info("Stopping stream...")
        return self.camera_controlpoint_handler.issue_cmd(self.CameraCpData.Commands.STOP_STREAM)

    def single_capture(self) -> bool:
        # logging.info("Taking single capture...")
        return self.camera_controlpoint_handler.issue_cmd(self.CameraCpData.Commands.SINGLE_CAPTURE)

    def get_image(self, numberOfStichedImages=1) -> np.ndarray | None:
        width = self._roi[2] - self._roi[0] + 1
        height = self._roi[3] - self._roi[1] + 1
        size = width * height * 2 * numberOfStichedImages
        raw_data = self._image_store.wait_and_pop(size, timeout=1.0)
        if raw_data is None:
            return None
        return np.frombuffer(raw_data, dtype=np.uint16).reshape((width * numberOfStichedImages, height))

    def get_mode(self) -> Optional[_AquisitionMode]:
        data = self.camera_controlpoint_handler.get_control(self.CameraCpData.SubCommands.MODE, 1)
        if data is not None:
            return self.AquisitionMode(data[0])
        return None

    def set_mode(self, mode: _AquisitionMode) -> bool:
        data = mode.value.to_bytes(1, 'big')
        return self.camera_controlpoint_handler.set_control(self.CameraCpData.SubCommands.MODE, data)

    def get_integration_time(self) -> Optional[int]:
        data = self.camera_controlpoint_handler.get_control(self.CameraCpData.SubCommands.INTEGRATION_TIME, 2)
        if data is not None:
            return int.from_bytes(data[0:2], 'big')
        return None

    def set_integration_time(self, integration_time: int) -> bool:
        data = integration_time.to_bytes(2, 'big')
        return self.camera_controlpoint_handler.set_control(self.CameraCpData.SubCommands.INTEGRATION_TIME, data)

    def get_roi(self) -> Optional[tuple[int, int, int, int]]:
        data = self.camera_controlpoint_handler.get_control(self.CameraCpData.SubCommands.ROI, 8)
        if data is not None:
            TopLeft_x = int.from_bytes(data[0:2], 'big')
            TopLeft_y = int.from_bytes(data[2:4], 'big')
            BottomRight_x = int.from_bytes(data[4:6], 'big')
            BottomRight_y = int.from_bytes(data[6:8], 'big')
            self._roi = (TopLeft_x, TopLeft_y, BottomRight_x, BottomRight_y)
            return self._roi
        return None

    def set_roi(self, roi: tuple[int, int, int, int]) -> bool:
        TopLeft_x = roi[0].to_bytes(2, 'big')
        TopLeft_y = roi[1].to_bytes(2, 'big')
        BottomRight_x = roi[2].to_bytes(2, 'big')
        BottomRight_y = roi[3].to_bytes(2, 'big')
        self._roi = roi
        data = TopLeft_x + TopLeft_y + BottomRight_x + BottomRight_y
        return self.camera_controlpoint_handler.set_control(self.CameraCpData.SubCommands.ROI, data)

    def get_modulation_frequency_hz(self) -> Optional[int]:
        data = self.camera_controlpoint_handler.get_control(self.CameraCpData.SubCommands.MODULATION_FREQUENCY, 4)
        if data is not None:
            return int.from_bytes(data[0:4], 'big')
        return None

    def set_modulation_frequency_hz(self, frequency_hz: int) -> bool:
        data = frequency_hz.to_bytes(4, 'big')
        return self.camera_controlpoint_handler.set_control(self.CameraCpData.SubCommands.MODULATION_FREQUENCY, data)

    def get_min_amplitude(self) -> Optional[int]:
        data = self.camera_controlpoint_handler.get_control(self.CameraCpData.SubCommands.MIN_AMPLITUDE, 2)
        if data is not None:
            return int.from_bytes(data[0:2], 'big')
        return None

    def set_min_amplitude(self, min_amplitude: int) -> bool:
        data = min_amplitude.to_bytes(2, 'big')
        return self.camera_controlpoint_handler.set_control(self.CameraCpData.SubCommands.MIN_AMPLITUDE, data)

    def get_compensation_phase_offset(self) -> Optional[bool]:
        data = self.camera_controlpoint_handler.get_control(self.CameraCpData.SubCommands.COMPENSATION_PHASE_OFFSET, 1)
        if data is not None:
            return data != 0
        return None
    
    def get_compensation_phase_error(self) -> Optional[bool]:
        data = self.camera_controlpoint_handler.get_control(self.CameraCpData.SubCommands.COMPENSATION_PHASE_ERROR, 1)
        if data is not None:
            return data != 0
        return None
    
    def get_compensation_temperature(self) -> Optional[bool]:
        data = self.camera_controlpoint_handler.get_control(self.CameraCpData.SubCommands.COMPENSATION_TEMPERATURE, 1)
        if data is not None:
            return data != 0
        return None
    
    def get_compensation_grayscale_dsnu(self) -> Optional[bool]:
        data = self.camera_controlpoint_handler.get_control(self.CameraCpData.SubCommands.COMPENSATION_GRAYSCALE_DSNU, 1)
        if data is not None:
            return data != 0
        return None

    def set_compensation_phase_offset(self, enabled: bool) -> bool:
        data = enabled.to_bytes(1, 'big')
        return self.camera_controlpoint_handler.set_control(self.CameraCpData.SubCommands.COMPENSATION_PHASE_OFFSET, data)

    def set_compensation_phase_error(self, enabled: bool) -> bool:
        data = enabled.to_bytes(1, 'big')
        return self.camera_controlpoint_handler.set_control(self.CameraCpData.SubCommands.COMPENSATION_PHASE_ERROR, data)
    
    def set_compensation_temperature(self, enabled: bool) -> bool:
        data = enabled.to_bytes(1, 'big')
        return self.camera_controlpoint_handler.set_control(self.CameraCpData.SubCommands.COMPENSATION_TEMPERATURE, data)
    
    def set_compensation_grayscale_dsnu(self, enabled: bool) -> bool:
        data = enabled.to_bytes(1, 'big')
        return self.camera_controlpoint_handler.set_control(self.CameraCpData.SubCommands.COMPENSATION_GRAYSCALE_DSNU, data)

class BluetoothDevice():

    def __init__(self, device_name, timeout=10, host_transport="usb:0", host_address=Address.ANY):
        self.timeout = timeout

        self._host_hci_transport = host_transport
        self._host_hci_address: Address = host_address
        self._hci_transport: Transport = None  # type: ignore
        self._hci_device: Device = None  # type: ignore
        self.peripheral_name = device_name
        self.peripheral_address: Address = None  # type: ignore
        self.peripheral_connection: Connection = None  # type: ignore
        self._peripheral_l2cap_channel: l2cap.LeCreditBasedChannel = None  # type: ignore

        self.loop = asyncio.new_event_loop()
        self.thread = threading.Thread(target=self._run_loop, name="ble device thread", daemon=True)
        self.thread.start()

        # Init bluetooth interface
        async def init_bluetooth_interface():
            self._hci_transport = await open_transport(self._host_hci_transport)
            self._hci_device = Device.with_hci('ble_client',
                                               self._host_hci_address,
                                               hci_source=self._hci_transport.source,
                                               hci_sink=self._hci_transport.sink)
            await self._hci_device.power_on()
        self._run_coroutine(init_bluetooth_interface())

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.loop and self.loop.is_running():
            self.loop.call_soon_threadsafe(self._stop_loop)
        if self.thread.is_alive():
            self.thread.join()

    def _run_loop(self):
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()
    
    def _stop_loop(self):
        for task in asyncio.all_tasks(self.loop):
            task.cancel()
        self.loop.stop()

    def _run_coroutine(self, coro):
        return asyncio.run_coroutine_threadsafe(coro, self.loop).result()

    def scan_for_devices_dict(self) -> list[dict]:
        found_devices = {}

        async def on_adv(advertisement: Advertisement):
            """Callback triggered on every received advertisement."""
            name = advertisement.data.get(AdvertisingData.Type.COMPLETE_LOCAL_NAME)
            if not name:
                name = "unknown"
            addr = advertisement.address.to_string(with_type_qualifier=True)
            if addr not in found_devices:
                rssi = getattr(advertisement, 'rssi', -127)
                found_devices[addr] = {
                    'address': addr,
                    'name': name,
                    'rssi': rssi
                }

        async def work():
            self._hci_device.add_listener('advertisement', on_adv)
            await self._hci_device.start_scanning(filter_duplicates=True)
            await asyncio.sleep(self.timeout)
            await self._hci_device.stop_scanning()
            self._hci_device.remove_listener('advertisement', on_adv)

        self._run_coroutine(work())
        return sorted(found_devices.values(), key=lambda x: x['rssi'], reverse=True)

    def scan_for_devices(self) -> list[str]:
        devices: list[str] = []

        async def on_adv(advertisement: Advertisement):
            """Callback triggered on every received advertisement."""
            new_device = advertisement.address.to_string(with_type_qualifier=True)
            if new_device not in devices:
                devices.append(new_device)

        async def work():
            self._hci_device.add_listener('advertisement', on_adv)
            await self._hci_device.start_scanning(filter_duplicates=True)
            await asyncio.sleep(self.timeout)
            await self._hci_device.stop_scanning()
            self._hci_device.remove_listener('advertisement', on_adv)

        self._run_coroutine(work())
        return devices

    def connect(self, device_address):
        self.peripheral_found = asyncio.Event()

        async def on_adv(advertisement: Advertisement):
            """Callback triggered on every received advertisement."""
            if ((advertisement.address.to_string(with_type_qualifier=False) == self.peripheral_address) or
                    (advertisement.address.to_string(with_type_qualifier=True) == self.peripheral_address)):
                await self._hci_device.stop_scanning()
                self.peripheral_found.set()
                # make sure we always use the address including type qualifier, even though the user did not explicitly set that
                self.peripheral_address = advertisement.address

        async def wait_for_peripheral():
            self._hci_device.add_listener('advertisement', on_adv)
            await self._hci_device.start_scanning()
            try:
                await asyncio.wait_for(self.peripheral_found.wait(), timeout=self.timeout)
            except asyncio.TimeoutError:
                print("Timeout: Target advertisement not seen.")
                return
            finally:
                self._hci_device.remove_listener('advertisement', on_adv)

        async def scan_for_services():
            peer = Peer(self.peripheral_connection)
            await peer.discover_services()
            for service in peer.services:
                await service.discover_characteristics()
                for characteristic in service.characteristics:
                    await characteristic.discover_descriptors()

        async def work(device_address):
            self.peripheral_address = device_address

            # Wait until the Peripheral is seen
            await wait_for_peripheral()

            # Connect to the Peripheral
            log.info(f"Connecting to {device_address}...")
            try:
                self.peripheral_connection = await self._hci_device.connect(peer_address=self.peripheral_address, timeout=self.timeout)
                log.debug("GATT connection established.")
            except Exception:
                self.peripheral_address = None  # type: ignore
                raise Exception(f"Failed to connect to device '{device_address}'")

            # Discover services
            await scan_for_services()

        self._run_coroutine(work(device_address))

    def disconnect(self):
        async def work():
            if self.peripheral_connection is not None:
                log.info(f"Disconnecting from {self.peripheral_address}...")
                await self.peripheral_connection.disconnect()
            await self._hci_device.power_off()
            await self._hci_transport.close()
            log.info("Disconnected.")

        self._run_coroutine(work())

    def is_connected(self):
        async def work():
            return len(self._hci_device.connections) > 0

        return self._run_coroutine(work())

    def print_services(self):
        peer = Peer(self.peripheral_connection)
        for service in peer.services:
            print(service)
            for characteristic in service.characteristics:
                print(f"  {characteristic}")
                for descriptor in characteristic.descriptors:
                    print(f"    {descriptor}")

    def register_notification(self, char_uuid, callback=None):
        async def work(char_uuid: UUID, callback):
            char = self._get_characteristics(char_uuid)
            await char.subscribe(callback, prefer_notify=False)
            log.debug(f"Subscribed {char_uuid}!")

        if callback is None:
            callback = self._on_notification

        self._run_coroutine(work(char_uuid, callback))

    def unregister_notification(self, char_uuid, callback=None):
        async def work(char_uuid: UUID, callback):
            char = self._get_characteristics(char_uuid)
            await char.unsubscribe(callback)
            log.debug(f"Unsubscribed {char_uuid}!")

        if callback is None:
            callback = self._on_notification

        self._run_coroutine(work(char_uuid, callback))

    def read_gatt_char(self, char_uuid):
        async def work(char_uuid: UUID):
            char = self._get_characteristics(char_uuid)
            return await char.read_value()

        return self._run_coroutine(work(char_uuid))

    def write_gatt_char(self, char_uuid, value):
        async def work(char_uuid: UUID, value):
            char = self._get_characteristics(char_uuid)
            await char.write_value(value)

        self._run_coroutine(work(char_uuid, value))

    # Public methods:
    def open_data_channel(self, callback=None, specs: Optional[l2cap.LeCreditBasedChannelSpec] = None):
        def on_data_received(data):
            """Callback for when data is received on the L2CAP channel."""
            log.info(f"<- L2CAP Data Received ({len(data)} bytes): {data.hex()}")

        async def work(callback, specs):
            self._peripheral_l2cap_channel = await self.peripheral_connection.create_l2cap_channel(specs)
            self._peripheral_l2cap_channel.sink = callback
            log.info(f"L2CAP CoC established.")

        if callback is None:
            callback = on_data_received

        if specs is None:
            specs = l2cap.LeCreditBasedChannelSpec(
                psm=0x0025,
                mtu=2048,
                mps=2048,
                max_credits=255,
            )

        self._run_coroutine(work(callback, specs))

    # Private methods:
    def _on_notification(self, data):
        """
        Callback function to handle incoming indications.
        """
        log.debug(f"  OpCode   : 0x{data.hex()[0:2]}")
        log.debug(f"  Command  : 0x{data.hex()[2:4]}")
        log.debug(f"  Response : 0x{data.hex()[4:6]}")

    def _get_characteristics(self, uuid: UUID) -> gatt_client.CharacteristicProxy[bytes]:
        peer = Peer(self.peripheral_connection)
        chars = peer.get_characteristics_by_uuid(uuid)
        if not chars:
            raise Exception("Characteristic not found!")
        return chars[0]
