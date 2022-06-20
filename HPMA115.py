import struct
import time
from enum import Enum
from typing import Callable, Optional

import serial


class CommandFailure(Exception):
    pass


class ChecksumFailure(Exception):
    pass


class SerialDataMalformed(Exception):
    pass


class PacketState(Enum):
    DATA = 1
    POSACK = 2
    NEGACK = 3


class Response(object):
    def __init__(self, state: PacketState, data: Optional[bytearray] = None):
        self.state = state
        self.data = data


class SampleC0(object):
    """
    A single data sample from the HPMA115C0.

    PM1_0: Particle count <=1um in ug/m^3
    PM2_5: Particle count <=2.5um in ug/m^3
    PM4_0: Particle count <=4um in ug/m^3
    PM10: Particle count <=10um in ug/m^3
    """

    def __init__(self, data):
        self.PM1_0 = data[0]
        self.PM2_5 = data[1]
        self.PM4_0 = data[2]
        self.PM10 = data[3]

    def __repr__(self):
        return f"PM1.0: {self.PM1_0}\nPM2.5: {self.PM2_5}\nPM4.0: {self.PM4_0}\nPM10: {self.PM10}"


class SampleS0(object):
    """
    A single data sample from the HPMA115S0.

    PM2_5: Particle count <=2.5um in ug/m^3
    PM10: Particle count <=10um in ug/m^3
    """

    def __init__(self, data):
        if len(data) == 2:
            self.PM2_5 = data[0]
            self.PM10 = data[1]
        elif len(data) == 13:
            self.PM2_5 = data[1]
            self.PM10 = data[2]

    def __repr__(self):
        return f"PM2.5: {self.PM2_5}\nPM10: {self.PM10}"


def _checksum(packet: bytes):
    return (65536 - sum(packet)) % 256


class HPMA115(object):
    """
    Base HPMA115 implementation.

    Do not instantiate directly, use either HPMA115C0 for the compact model or HPMA115S0 for the original model.
    """
    SampleCls = None

    def __init__(self, port: str):
        """
        Creates a new HPMA115 interface.

        :param port: The path to the serial device to use to communicate with the HPMA115 module
        """
        self.ser = serial.Serial(port, baudrate=9600, timeout=100)
        self._send(0x20)
        self._send(0x02)
        time.sleep(0.2)
        self.ser.reset_input_buffer()

    def _send(self, command: int, data: Optional[bytes] = None):
        packet = bytearray()
        packet.append(0x68)  # Header
        if data is not None:
            packet.append(len(data) + 1)  # Length
        else:
            packet.append(0x01)  # No Data Length
        packet.append(command)
        if data is not None:
            packet += data
        packet.append(_checksum(packet))
        # print("Send: " + str(packet.hex()))
        self.ser.write(packet)

    def _recv(self) -> Response:
        header = self.ser.read(2)
        if header[0] == 0x40:
            data = self.ser.read(header[1])
            cs = int.from_bytes(self.ser.read(1), "big")
            if cs != _checksum(header + data):
                raise ChecksumFailure()
            else:
                # print("Recv: " + str((header + data + bytes(cs)).hex()))
                return Response(PacketState.DATA, data[1:])
        elif header[0] == 0x42 and header[1] == 0x4D:
            data = self.ser.read(28)
            cs = struct.unpack(">H", self.ser.read(2))[0]
            calc_cs = sum(header + data) % 65536
            if cs != calc_cs:
                raise ChecksumFailure()
            else:
                # print("Recv: " + str((header + data + bytes(cs)).hex()))
                return Response(PacketState.DATA, data[2:])
        elif header[0] == 0xA5 and header[1] == 0xA5:
            # print("Recv: PosAck")
            return Response(PacketState.POSACK)
        elif header[0] == 0x96 and header[1] == 0x96:
            # print("Recv: NegAck")
            return Response(PacketState.NEGACK)
        else:
            self.ser.reset_input_buffer()
            raise SerialDataMalformed()

    def stop_measurement(self):
        """
        Stops measurement, this will prolong device life due to shutting down the onboard fan, but sampling will be disabled until the measurement is enabled.
        """
        self._send(0x02)
        if self._recv().state == PacketState.NEGACK:
            raise CommandFailure()

    def start_measurement(self):
        """
        Triggers measurement to begin on the device, required for the sample method to function.
        """
        self._send(0x01)
        if self._recv().state == PacketState.NEGACK:
            raise CommandFailure()

    def sample(self) -> "Self.SampleCls":
        """
        Retrieves a single sample from the device as long as measurement is currently active.

        :return:
        """
        self._send(0x04)
        rsp = self._recv()
        if rsp.state == PacketState.NEGACK:
            raise CommandFailure()
        else:
            return self.SampleCls(struct.unpack(">HHHHHH", rsp.data))

    def set_cust_adj_coeff(self, coeff: int):
        """
        Sets the customer adjustment coefficient.

        :param coeff: New value for the coefficient, should be between 30 and 200 inclusive.
        """
        if coeff < 30 or coeff > 200:
            raise ValueError("coeff value out of range, must be between 30 and 200")
        self._send(0x08, bytes([coeff]))
        if self._recv().state == PacketState.NEGACK:
            raise CommandFailure()

    def read_cust_adj_coeff(self) -> int:
        """
        Reads the current value of the customer adjustment coefficient.

        :return: The customer adjustment coefficient
        """
        self._send(0x10)
        rsp = self._recv()
        if rsp.state == PacketState.NEGACK:
            raise CommandFailure()
        else:
            return int.from_bytes(rsp.data, "big")

    def autosample(self, callback: Callable[["Self.SampleCls"], bool]):
        """
        Enables autosampling mode, passing each received sample to the provided callback. If the callback returns false the sampling is disabled, otherwise the sampling continues.

        :param callback: Called for each sample provided by the module, return value dictates if sampling continues.
        """
        self._send(0x40)
        if self._recv().state == PacketState.NEGACK:
            raise CommandFailure()
        while True:
            rsp = self._recv()
            if rsp.state == PacketState.NEGACK:
                raise CommandFailure()
            if not callback(self.SampleCls(struct.unpack(">HHHHHHHHHHHHH", rsp.data))):
                self._send(0x20)
                time.sleep(0.2)
                self.ser.reset_input_buffer()
                break


class HPMA115C0(HPMA115):
    SampleCls = SampleC0


class HPMA115S0(HPMA115):
    SampleCls = SampleS0


def test():
    sens = HPMA115C0("/dev/ttyACM0")

    _coeff = sens.read_cust_adj_coeff()
    print(_coeff)
    sens.set_cust_adj_coeff(195)
    print(sens.read_cust_adj_coeff())
    sens.set_cust_adj_coeff(_coeff)

    sens.start_measurement()
    for i in range(5):
        print(sens.sample())
        time.sleep(1)

    x = 0

    def repl(sample):
        global x
        print(sample)
        x += 1
        return x < 5

    sens.autosample(repl)


if __name__ == "__main__":
    test()
