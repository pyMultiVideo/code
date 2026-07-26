"""Module for controlling trigger pulse output on a MicroPython board from the GUI."""

import time
import serial
from serial.tools import list_ports
from inspect import getsource

# Pyboard class for communicating with a MicroPython board over a serial connection.
# Adapted from https://github.com/micropython/micropython/blob/master/tools/pyboard.py


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
            self.serial.write(command_bytes[i : min(i + 256, len(command_bytes))])
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


# PyboardManager -----------------------------------------------------------------------------


class PyboardManager:
    """Manage Pyboard discovery, connection and trigger pulse lifecycle."""

    def __init__(self):
        self.pyboard = None
        self.pyboard_port = None
        self.pulse_running = False
        self.last_error = ""
        self._checked_ports = set()
        self._pyboard_ports = set()

    def get_available_ports(self) -> list[str]:
        """Return detected board ports, keeping active port visible while pulsing."""
        active_port = self.pyboard_port if self.pulse_running else ""
        candidate_ports = [c[0] for c in list_ports.comports() if ("Pyboard" in c[1]) or ("USB Serial Device" in c[1])]
        for port in candidate_ports:
            if port in self._checked_ports:
                continue
            if _check_if_pyboard(port):
                self._pyboard_ports.add(port)
            self._checked_ports.add(port)
        pyboard_ports = [port for port in candidate_ports if port in self._pyboard_ports]
        if active_port and active_port not in pyboard_ports:
            pyboard_ports = [active_port] + pyboard_ports
        return pyboard_ports

    def connect(self, port: str) -> bool:
        """Connect to the selected board port, reusing existing connection when possible."""
        selected_port = str(port).strip()
        if not selected_port:
            self.last_error = "No trigger output port selected."
            return False

        if self.pyboard is not None and self.pyboard_port == selected_port:
            return True
        self.disconnect()
        try:
            self.pyboard = Pyboard(selected_port)
            self.pyboard_port = selected_port
            self.last_error = ""
            return True
        except (PyboardError, serial.SerialException, OSError) as exc:
            self.last_error = f"Could not open pyboard on {selected_port}: {exc}"
            self.disconnect()
            return False

    def disconnect(self):
        """Close the current board connection, if any."""
        if self.pyboard is None:
            return
        try:
            self.pyboard.close()
        except (PyboardError, serial.SerialException, OSError):
            pass
        self.pyboard = None
        self.pyboard_port = None

    def start_pulse(self, pin, frequency_hz: int) -> bool:
        """Start trigger pulse output on the currently connected board."""
        if self.pyboard is None:
            self.last_error = "Trigger board is not connected."
            return False
        try:
            self.pyboard.enter_raw_repl()
            self.pyboard.exec(getsource(_pyboard_enable_pulses))
            self.pyboard.exec_raw_no_follow(f"_pyboard_enable_pulses({pin!r}, {float(frequency_hz)})")
            self.pulse_running = True
            self.last_error = ""
            return True
        except PyboardError as exc:
            self.last_error = f"Could not start trigger pulses: {exc}"
            self.pulse_running = False
            self.disconnect()
            return False

    def stop_pulse(self) -> bool:
        """Stop trigger pulse output and release board resources."""
        if not self.pyboard:
            self.pulse_running = False
            return True
        stopped_cleanly = True
        try:
            self.pyboard.serial.write(b"\x03")
            try:
                output, output_err = self.pyboard.follow(timeout=2)
            finally:
                self.pyboard.exit_raw_repl()
            if output_err and b"KeyboardInterrupt" not in output_err:
                raise PyboardError("exception", output, output_err)
        except (PyboardError, serial.SerialException, OSError) as exc:
            self.last_error = f"Could not stop trigger pulses: {exc}"
            stopped_cleanly = False
        finally:
            self.pulse_running = False
            self.disconnect()
        return stopped_cleanly


# Helper functions. ---------------------------------------------------------------------------


def _check_if_pyboard(port):
    """Return True if the given port is a Pyboard, False otherwise."""
    try:
        board = Pyboard(port)
        board.enter_raw_repl()
        board.close()
        return True
    except (PyboardError, serial.SerialException):
        return False


def _pyboard_enable_pulses(pin, frequency_hz):
    """Used on pyboard to toggle pin at 50% duty cycle until KeyboardInterrupt."""
    import time
    from machine import Pin

    period_us = int(1e6 / frequency_hz)
    on_off_dur = period_us // 2
    try:
        pin = int(pin)
    except ValueError:
        pass  # pin is a string, not an int
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
