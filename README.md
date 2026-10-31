# sei-bus-encoder-reader

A small, standalone Python tool to read a single absolute encoder on a
**SEI (Serial Encoder Interface) bus** — the kind used by US Digital
absolute encoder products — over a plain serial/USB-serial connection, and
print its position as a heading in degrees.

No vendor tracking/rotor software required. This talks to the bus
directly.

## What this is for

Antenna rotator and dish-tracker builds that use SEI-bus absolute encoders
(e.g. for azimuth/elevation feedback) sometimes need a quick, independent
way to verify what an encoder is actually reporting — for calibration,
troubleshooting a rotator controller, or bringing up a new axis — without
depending on whatever proprietary tracking software is normally driving
it.

This tool does one thing: poll one encoder address and print the current
heading. It is read-only — it never writes to the bus, so it's safe to run
alongside other software that's actively driving the same bus (as long as
nothing else is also trying to read at the exact same moment; see
Limitations).

## Protocol

SEI bus encoders share a single serial line (9600 baud, 8N1) and are
addressed by a small integer (commonly 0 and 1 for two axes, e.g.
azimuth/elevation).

**Read command:**

| Direction | Bytes | Meaning |
|---|---|---|
| TX | `0x10 + address` | 1 byte, requests current position |
| RX | 2 bytes | big-endian `uint16` raw pulse count |

That's the entire read-side protocol — the bus has no "identify yourself"
or "report your resolution" command. The encoder's pulses-per-revolution
(PPR) and mechanical offset are properties of your installation (gearing,
mounting, mechanical zero point), not something the bus tells you, so you
supply them as parameters.

## Installation

```bash
pip install pyserial
```

Tested with Python 3.9+. No other dependencies.

## Usage

```bash
python3 sei_encoder_heading.py --port /dev/ttyUSB0 --addr 0 --ppr 44952
```

```
pulses=14392  heading= 115.26 deg
pulses=14393  heading= 115.27 deg
...
```

### Arguments

| Flag | Required | Description |
|---|---|---|
| `--port` | yes | Serial device, e.g. `/dev/ttyUSB0` (Linux) or `COM3` (Windows) |
| `--addr` | yes | SEI bus address of the encoder to read (integer, typically 0 or 1) |
| `--ppr` | yes | Pulses per 360 degrees for this encoder/axis — see Calibration below |
| `--reverse` | no | Reverse the counting direction |
| `--offset` | no | Degrees added after conversion, e.g. to correct a known mechanical zero-point offset (default `0`) |
| `--interval` | no | Seconds between reads; `0` reads once and exits (default `1`) |

On Windows, replace `/dev/ttyUSB0` with the appropriate `COMn` port.

## Setting a true-north (or other absolute) reference

The encoder's own raw zero point is wherever it happened to be when it
was mounted — it has no idea where true north is. `--offset` is also how
you correct for this: once you know how far off the readout is from the
real-world reference, add (or subtract) that amount.

Example: the mount's mechanical zero points 15 degrees east of true
north, so without correction the tool reads `15.0` while the antenna is
actually pointing at `0.0` (north). Fix it with:

```bash
python3 sei_encoder_heading.py --port /dev/ttyUSB0 --addr 0 --ppr 44952 --offset -15
```

Negative offsets wrap correctly (e.g. a raw `5.0` with `--offset -15`
reads as `350.0`, not `-10.0`).

## Calibration — don't trust a nameplate/config PPR blindly

The bus gives you a raw pulse count with no resolution information
attached. Any PPR figure that came from a datasheet, a config file, or a
previous project is only a starting guess if there's gearing or an
actuator linkage between the encoder shaft and the thing you're actually
measuring — the encoder's native PPR and the PPR you need for "degrees of
the output shaft" are not necessarily the same number.

To calibrate reliably:

1. Move the axis to two (ideally three, spanning the full range) known
   reference positions.
2. Read the raw pulse count at each with `--ppr 1 --interval 0` (so the
   script just prints the raw count).
3. Fit `degrees = (pulses / ppr) + offset` across your reference points
   and solve for `ppr`/`offset`.
4. Confirm with a third point before trusting the result — a two-point fit
   can hide a wrong assumption about linearity across the full range.

## Limitations

- Read-only — this tool never drives relays or PWM outputs, and has no
  motor-control support.
- Single encoder per invocation. Run two instances (one per `--port`/
  `--addr` pair) if you need both axes at once, or adapt the script.
- The serial port is single-owner at the OS level — stop any other
  software that also has the port open before running this, or you'll get
  read conflicts.
- No retry/reconnect logic — if the serial device disappears, the script
  exits with an error.

## License

MIT — see [LICENSE](LICENSE).
