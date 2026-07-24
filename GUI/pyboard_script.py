import time
import serial
from serial.tools import list_ports
from inspect import getsource

# Pyboard class


class PyboardError(BaseException):
    pass


class Pyboard:
    def __init__(self, serial_device, baudrate=115200):
        self.serial = serial.Serial(serial_device, baudrate=baudrate, interCharTimeout=1)

    def close(self):
        self.serial.close()

    def read_until(self, min_num_bytes, ending, timeout=10):
        data = self.serial.read(min_num_bytes)
        timeout_count = 0
        while True:
            if data.endswith(ending):
                break
            elif self.serial.inWaiting() > 0:
                new_data = self.serial.read(1)
                data = data + new_data
                # time.sleep(0.01)
                timeout_count = 0
            else:
                timeout_count += 1
                if timeout is not None and timeout_count >= 10 * timeout:
                    break
                time.sleep(0.1)
        return data

    def enter_raw_repl(self):
        self.serial.write(b"\r\x03\x03")  # ctrl-C twice: interrupt any running program
        # flush input (without relying on serial.flushInput())
        n = self.serial.inWaiting()
        while n > 0:
            self.serial.read(n)
            n = self.serial.inWaiting()
        self.serial.write(b"\r\x01")  # ctrl-A: enter raw REPL
        data = self.read_until(1, b"to exit\r\n>")
        if not data.endswith(b"raw REPL; CTRL-B to exit\r\n>"):
            print(data)
            raise PyboardError("could not enter raw repl")
        self.serial.write(b"\x04")  # ctrl-D: soft reset
        data = self.read_until(1, b"to exit\r\n>")
        if not data.endswith(b"raw REPL; CTRL-B to exit\r\n>"):
            print(data)
            raise PyboardError("could not enter raw repl")

    def exit_raw_repl(self):
        self.serial.write(b"\r\x02")  # ctrl-B: enter friendly REPL

    def follow(self, timeout):
        # wait for normal output
        data = self.read_until(1, b"\x04", timeout=timeout)
        if not data.endswith(b"\x04"):
            raise PyboardError("timeout waiting for first EOF reception")
        data = data[:-1]

        # wait for error output
        data_err = self.read_until(2, b"\x04>", timeout=timeout)
        if not data_err.endswith(b"\x04>"):
            raise PyboardError("timeout waiting for second EOF reception")
        data_err = data_err[:-2]

        # return normal and error output
        return data, data_err

    def exec_raw_no_follow(self, command):
        if isinstance(command, bytes):
            command_bytes = command
        else:
            command_bytes = bytes(command, encoding="utf8")

        # write command
        for i in range(0, len(command_bytes), 256):
            self.serial.write(command_bytes[i:min(i + 256, len(command_bytes))])
            time.sleep(0.01)
        self.serial.write(b"\x04")

        # check if we could exec command
        data = self.serial.read(2)
        if data != b"OK":
            raise PyboardError("could not exec command")

    def exec_raw(self, command, timeout=10):
        self.exec_raw_no_follow(command)
        return self.follow(timeout)

    def exec(self, command):
        ret, ret_err = self.exec_raw(command)
        if ret_err:
            raise PyboardError("exception", ret, ret_err)
        return ret


# Helper functions.


def check_if_pyboard(port):
    """Return True if the given port is a Pyboard, False otherwise."""
    try:
        board = Pyboard(port)
        board.enter_raw_repl()
        board.close()
        return True
    except (PyboardError, serial.SerialException):
        return False


def list_connected_pyboards():
    """Return a list of serial ports that appear to be MicroPython boards."""
    ports = [c[0] for c in list_ports.comports() if ("Pyboard" in c[1]) or ("USB Serial Device" in c[1])]
    return [port for port in ports if check_if_pyboard(port)]


def _pyboard_enable_pulses(pin, frequency_hz):
    """Used on pyboard to toggle pin at 50% duty cycle until KeyboardInterrupt."""
    import time
    from machine import Pin

    period_us = int(1e6 / frequency_hz)
    on_off_dur = period_us // 2
    pulse_pin = Pin(pin, Pin.OUT)
    try:
        while True:
            pulse_pin.value(1)
            time.sleep_us(on_off_dur)
            pulse_pin.value(0)
            time.sleep_us(on_off_dur)
    except KeyboardInterrupt:
        pass
    finally:
        pulse_pin.value(0)


def start_pulse_output(pyboard, pin, frequency_hz):
    """Start continuous pulse output on MicroPython pin."""
    pyboard.enter_raw_repl()
    try:
        pyboard.exec(getsource(_pyboard_enable_pulses))
        pyboard.exec_raw_no_follow(f"_pyboard_enable_pulses({pin!r}, {float(frequency_hz)})")
    except Exception:
        pyboard.exit_raw_repl()
        raise


def stop_pulse_output(pyboard, timeout=2):
    """Stop running pulse loop by sending KeyboardInterrupt (Ctrl-C)."""
    pyboard.serial.write(b"\x03")
    try:
        output, output_err = pyboard.follow(timeout=timeout)
    finally:
        pyboard.exit_raw_repl()

    if output_err and b"KeyboardInterrupt" not in output_err:
        raise PyboardError("exception", output, output_err)

    return output


if __name__ == "__main__":
    pyboard_ports = list_connected_pyboards()
    if not pyboard_ports:
        raise RuntimeError("No connected pyboard found")

    pyboard = Pyboard(pyboard_ports[0])
    start_pulse_output(pyboard, pin="B4", frequency_hz=5)
    time.sleep(2)
    stop_pulse_output(pyboard)
    pyboard.close()
