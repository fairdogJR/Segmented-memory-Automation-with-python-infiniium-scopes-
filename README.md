# U of T Pulse Capture Example

Python tools for configuring Keysight/Agilent oscilloscopes for segmented waveform acquisition and downloading captured data via VISA/SCPI commands.

## Main GUI Applications

### `scope_setup_and_viewer.py`
**Complete oscilloscope control and visualization tool**
- Configure scope parameters (channel scale, timebase, trigger, sample rate, segment count)
- Trigger single acquisitions
- Download and visualize segments with playback controls
- Interactive matplotlib plots with navigation (first, prev, play, next, last)

### `segment_viewer_gui.py`
**Simplified segment viewer**
- Connect to scope and query instrument ID
- Download segments from existing acquisitions
- Playback controls for viewing waveforms
- Trigger new single acquisitions

## Dependencies

### Required
- **Python 3.12+**
- **PyVISA** - VISA instrument communication
- **NumPy** - Numerical processing and waveform data handling
- **Matplotlib** - Waveform visualization and plotting
- **Tkinter** - GUI framework (usually included with Python)

### VISA Backend (Required)
PyVISA requires a VISA backend installed separately:
- NI-VISA (National Instruments), or
- Keysight IO Libraries Suite

Install via pip:
```bash
pip install -r requirements.txt
```

## Quick Start

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Launch the full GUI:**
   ```bash
   python scope_setup_and_viewer.py
   ```

3. **Connect to your scope:**
   - Enter VISA resource (e.g., `TCPIP0::192.168.0.2::inst0::INSTR`)
   - Click **Connect**

4. **Configure and capture:**
   - Adjust setup parameters as needed
   - Click **Configure Scope**
   - Click **Capture New Data** to trigger
   - Click **Collect Segments** to download

## Reference Examples

*Note: The following example scripts were not covered in the January 16, 2026 presentation but are included as reference implementations.*

### `seg_pulse_capture_UofT_example.py`
Refactored class-based implementation demonstrating:
- `Scope`: Connection and SCPI helpers
- `Setup`: Configuration without triggering
- `CaptureRoutine`: Single acquisition triggering
- `SegmentDownloader`: Segment download and basic plotting

### `data_transfer_seg_data_example.py`
Low-level segment data transfer examples:
- IEEE 488.2 binary block parsing
- Mode A: Per-segment sequential download
- Mode B: Bulk transfer with `:WAVeform:SEGMented:ALL ON`
- Handles partial reads and large waveforms

### `super_simple_pulse_from_command_expert.py`
Minimal example generated from Keysight Command Expert:
- Direct SCPI command sequence
- Basic scope configuration
- Single acquisition trigger
- Useful as reference for SCPI syntax

### `simple_linear_example.py`
Basic linear acquisition example (non-segmented mode)

## Additional Examples

The `other example code/` directory contains additional demonstration scripts from various testing scenarios. These are included as reference examples:

- **DEMO1-simple_risetime_MXR_SCOPE.py** - Basic rise time measurement with MXR scope
- **DEMO1-supp_simple_risetime_hsdsCommand ExpertSequence.iseqx** - Command Expert sequence for DEMO1
- **DEMO2-simple_risetime_MXR_Scope_hsdsGUI.py** - Rise time measurement with GUI
- **DEMO4-flexdca_offlineHSDS2025.py** - FlexDCA offline analysis
- **DEMO4-supp--recordedSCPI.txt** - Recorded SCPI commands for DEMO4
- **DEMO5-M8040_halting python_when bertis in BUSY stateTEST.py** - M8040 BERT synchronization example

*These examples demonstrate various instrument control patterns and measurement techniques.*

## SCPI Commands Used

**Instrument:**
- `*IDN?` - Query instrument identification
- `*RST` - Reset to default state

**Channel & Timebase:**
- `:CHANnel1:SCALe` - Vertical scale (V/div)
- `:TIMebase:SCALe` - Horizontal scale (s/div)
- `:TIMebase:POSition` - Time reference position
- `:TRIGger:LEVel` - Trigger threshold

**Acquisition:**
- `:ACQuire:MODE SEGMented` - Enable segmented mode
- `:ACQuire:SRATe:ANALog` - Sample rate
- `:ACQuire:POINts:ANALog` - Points per segment
- `:ACQuire:SEGMented:COUNt` - Number of segments
- `:SINGle` - Trigger single acquisition

**Waveform Transfer:**
- `:WAVeform:SOURce` - Select channel
- `:WAVeform:FORMat` - Data format (WORD = 16-bit)
- `:WAVeform:BYTeorder` - Byte order (LSBF/MSBF)
- `:WAVeform:DATA?` - Download waveform data
- `:WAVeform:SEGMented:COUNt?` - Query captured segments
- `:WAVeform:SEGMented:TTAG?` - Get segment time tag
- `:WAVeform:XINCrement?` - Time increment per point
- `:ACQuire:SEGMented:INDex` - Select segment

## Notes
- Segment count queried may differ from configured if acquisition stopped early
- IEEE 488.2 binary block format requires proper parsing for large transfers
- Time tags are relative to first segment
- Raw ADC values (int16) can be converted to voltage using scope parameters
