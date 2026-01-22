# U of T Pulse Capture Example (Refactored)

This refactors the original script into classes and separates instrument setup, capture, and segmented waveform download/display.

## Prerequisites
- Python 3.12+
- PyVISA (requires a VISA backend like NI-VISA or Keysight IO Libraries)
- Optional: NumPy and Matplotlib for plotting

## Install dependencies
```
pip install -r requirements.txt
```
Note: PyVISA needs a VISA backend installed separately (not via pip). Install NI-VISA or Keysight IO Libraries Suite.

## Configure
Edit `MXR_IP` in `seg_pulse_capture_UofT_example.py` to match your scope's IP.

## Run
This will:
- Connect and apply setup (segmented acquisition configuration)
- Trigger a single capture
- Download a subset of segments
- Display a quick summary or plot (if available)
```
python seg_pulse_capture_UofT_example.py
```

## Classes
- `Scope`: Connection and SCPI helpers
- `Setup`: Applies setup commands (without `:SINGLE`)
- `CaptureRoutine`: Sends `:SINGLE` and waits briefly
- `SegmentDownloader`: Downloads segments and displays summary/plots

## Notes
- Segment count queried is the configured count; actual acquired segments depend on triggers.
- Plotting requires `numpy` + `matplotlib`. If not installed, a textual summary is printed.
