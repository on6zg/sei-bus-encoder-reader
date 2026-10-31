#!/usr/bin/env python3
"""Read one SEI-bus absolute encoder and print its heading in degrees.

Usage:
    python3 sei_encoder_heading.py --port /dev/ttyUSB0 --addr 0 --ppr 44952
    python3 sei_encoder_heading.py --port COM3 --addr 1 --ppr 55393 --reverse
"""

import argparse
import sys
import time

import serial

BAUDRATE = 9600
READ_TIMEOUT = 0.5


def read_position(ser: serial.Serial, addr: int) -> int:
    ser.reset_input_buffer()
    ser.write(bytes([0x10 + addr]))
    reply = ser.read(2)
    if len(reply) != 2:
        raise TimeoutError(f"no reply from encoder at addr {addr}")
    return int.from_bytes(reply, byteorder="big")


def pulses_to_degrees(pulses: int, ppr: int, reverse: bool) -> float:
    deg = (pulses % ppr) / ppr * 360.0
    if reverse:
        deg = (360.0 - deg) % 360.0
    return deg


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", required=True, help="serial device, e.g. /dev/ttyUSB0 or COM3")
    parser.add_argument("--addr", type=int, required=True, help="SEI bus address (0 or 1)")
    parser.add_argument("--ppr", type=int, required=True, help="pulses per 360 degrees")
    parser.add_argument("--reverse", action="store_true", help="reverse counting direction")
    parser.add_argument("--offset", type=float, default=0.0, help="degrees offset applied after conversion")
    parser.add_argument("--interval", type=float, default=1.0, help="seconds between reads (0 = read once)")
    args = parser.parse_args()

    ser = serial.Serial(args.port, BAUDRATE, timeout=READ_TIMEOUT)
    time.sleep(1.0)  # let the port settle; do not force dtr/rts here

    try:
        while True:
            try:
                pulses = read_position(ser, args.addr)
                deg = (pulses_to_degrees(pulses, args.ppr, args.reverse) + args.offset) % 360.0
                print(f"pulses={pulses:5d}  heading={deg:7.2f} deg")
            except TimeoutError as exc:
                print(f"error: {exc}", file=sys.stderr)

            if args.interval <= 0:
                break
            time.sleep(args.interval)
    except KeyboardInterrupt:
        pass
    finally:
        ser.close()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
