import numpy as np
import pyvisa
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import tkinter as tk
from tkinter import ttk
import threading


def _read_ieee_block_from_instrument(inst) -> bytes:
    """Read IEEE 488.2 definite-length binary block from instrument."""
    header = inst.read_bytes(2)
    if header[0:1] != b"#":
        raise ValueError("Not an IEEE block (missing '#').")
    
    nd = int(chr(header[1]))
    if nd <= 0:
        raise ValueError(f"Invalid IEEE block ndigits={nd}")
    
    len_bytes = inst.read_bytes(nd)
    nbytes = int(len_bytes.decode("ascii"))
    
    payload = bytearray()
    remaining = nbytes
    while remaining > 0:
        chunk = inst.read_bytes(remaining)
        payload.extend(chunk)
        remaining = nbytes - len(payload)
    
    try:
        inst.read_bytes(1)
    except:
        pass
    
    return bytes(payload)


def connect_scope(resource: str, timeout_ms: int = 30000):
    rm = pyvisa.ResourceManager()
    inst = rm.open_resource(resource)
    inst.timeout = timeout_ms
    inst.write_termination = "\n"
    inst.read_termination = None
    inst.chunk_size = 1024 * 1024
    return inst


def setup_scope_acquisition(resource: str, channel_scale: float, timebase_scale: float,
                           trigger_level: float, timebase_position: float,
                           sample_rate: str, acquire_points: int, segment_count: int):
    """Configure scope for segmented acquisition"""
    inst = connect_scope(resource)
    try:
        inst.read_termination = "\n"
        inst.write('*RST')
        inst.write(f':CHANnel1:SCALe {channel_scale}')
        inst.write(f':TIMebase:SCALe {timebase_scale}')
        inst.write(f':TRIGger:LEVel CHANNEL1,{trigger_level}')
        inst.write(f':TIMebase:POSition {timebase_position}')
        inst.write(':ACQuire:MODE SEGMented')
        inst.write(f':ACQuire:SRATe:ANALog {sample_rate}')
        inst.write(f':ACQuire:POINts:ANALog {acquire_points}')
        inst.write(f':ACQuire:SEGMented:COUNt {segment_count}')
    finally:
        inst.close()


def setup_waveform_transfer(inst, source="CHANnel1", fmt="WORD", byteorder="LSBF"):
    inst.write(f":WAVeform:SOURce {source}")
    inst.write(f":WAVeform:FORMat {fmt}")
    inst.write(f":WAVeform:BYTeorder {byteorder}")


def query_captured_segment_count(inst) -> int:
    return int(float(inst.query(":WAVeform:SEGMented:COUNt?").strip()))


def query_timebase(inst):
    xincr = float(inst.query(":WAVeform:XINCrement?").strip())
    return xincr


def read_segment_word(inst, seg_index: int):
    inst.write(f":ACQuire:SEGMented:INDex {seg_index}")
    inst.write(":WAVeform:DATA?")
    payload = _read_ieee_block_from_instrument(inst)
    y = np.frombuffer(payload, dtype=np.int16)
    inst.read_termination = "\n"
    ttag = float(inst.query(":WAVeform:SEGMented:TTAG?").strip())
    inst.read_termination = None
    return y, ttag


def extract_segments_mode_a(resource: str, source="CHANnel1", start_segment=1, num_segments=10):
    inst = connect_scope(resource)
    try:
        inst.read_termination = "\n"
        setup_waveform_transfer(inst, source=source, fmt="WORD", byteorder="LSBF")
        xincr = query_timebase(inst)
        total_segs = query_captured_segment_count(inst)
        
        end_segment = min(start_segment + num_segments - 1, total_segs)
        
        inst.read_termination = None
        segments = []

        for i in range(start_segment, end_segment + 1):
            y, ttag = read_segment_word(inst, i)
            t = np.arange(len(y)) * xincr
            segments.append({"index": i, "ttag_s": ttag, "t_s": t, "y_raw": y})

        return segments, total_segs
    finally:
        inst.close()


def get_instrument_id(resource: str):
    """Query instrument identification"""
    inst = connect_scope(resource)
    try:
        inst.read_termination = "\n"
        idn = inst.query("*IDN?").strip()
        return idn
    finally:
        inst.close()


def trigger_single_acquisition(resource: str):
    """Trigger single acquisition on scope"""
    inst = connect_scope(resource)
    try:
        inst.read_termination = "\n"
        inst.write(":SINGle")
    finally:
        inst.close()


class ScopeSetupAndViewerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Oscilloscope Setup & Segment Viewer")
        self.root.geometry("1400x900")
        
        self.visa_resource = None
        self.segments = []
        self.current_index = 0
        self.is_playing = False
        self.play_speed = 500
        self.connected = False
        self.total_segments_available = 0
        
        self._create_widgets()
    
    def _create_widgets(self):
        # Connection panel
        conn_frame = ttk.LabelFrame(self.root, text="Connection", padding="10")
        conn_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=5)
        
        ttk.Label(conn_frame, text="VISA Resource:").pack(side=tk.LEFT, padx=5)
        self.ip_var = tk.StringVar(value="TCPIP0::10.81.185.89::inst0::INSTR")
        self.ip_entry = ttk.Entry(conn_frame, textvariable=self.ip_var, width=40)
        self.ip_entry.pack(side=tk.LEFT, padx=5)
        
        self.connect_btn = ttk.Button(conn_frame, text="Connect", command=self.connect_scope, width=12)
        self.connect_btn.pack(side=tk.LEFT, padx=5)
        
        self.idn_label = ttk.Label(conn_frame, text="Not connected", font=("Arial", 9), foreground="gray")
        self.idn_label.pack(side=tk.LEFT, padx=10)
        
        # Setup panel
        setup_frame = ttk.LabelFrame(self.root, text="Scope Setup Parameters", padding="10")
        setup_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=5)
        
        # Left column
        left_col = ttk.Frame(setup_frame)
        left_col.pack(side=tk.LEFT, padx=10)
        
        ttk.Label(left_col, text="Channel 1 Scale (V/div):").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.ch_scale_var = tk.DoubleVar(value=0.2)
        ttk.Entry(left_col, textvariable=self.ch_scale_var, width=15).grid(row=0, column=1, padx=5)
        
        ttk.Label(left_col, text="Timebase Scale (s/div):").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.tb_scale_var = tk.DoubleVar(value=2e-8)
        ttk.Entry(left_col, textvariable=self.tb_scale_var, width=15).grid(row=1, column=1, padx=5)
        
        ttk.Label(left_col, text="Trigger Level (V):").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.trig_level_var = tk.DoubleVar(value=0.32)
        ttk.Entry(left_col, textvariable=self.trig_level_var, width=15).grid(row=2, column=1, padx=5)
        
        ttk.Label(left_col, text="Timebase Position (s):").grid(row=3, column=0, sticky=tk.W, pady=2)
        self.tb_pos_var = tk.DoubleVar(value=0.0)
        ttk.Entry(left_col, textvariable=self.tb_pos_var, width=15).grid(row=3, column=1, padx=5)
        
        # Right column
        right_col = ttk.Frame(setup_frame)
        right_col.pack(side=tk.LEFT, padx=10)
        
        ttk.Label(right_col, text="Sample Rate:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.srate_var = tk.StringVar(value="MAX")
        srate_combo = ttk.Combobox(right_col, textvariable=self.srate_var, width=12)
        srate_combo['values'] = ('MAX', '10e9', '5e9', '2.5e9', '1e9', '500e6')
        srate_combo.grid(row=0, column=1, padx=5)
        
        ttk.Label(right_col, text="Acquire Points:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.acq_pts_var = tk.IntVar(value=1500)
        ttk.Entry(right_col, textvariable=self.acq_pts_var, width=15).grid(row=1, column=1, padx=5)
        
        ttk.Label(right_col, text="Segment Count:").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.seg_count_var = tk.IntVar(value=65536)
        ttk.Entry(right_col, textvariable=self.seg_count_var, width=15).grid(row=2, column=1, padx=5)
        
        # Setup button
        self.setup_btn = ttk.Button(setup_frame, text="Configure Scope", 
                                    command=self.configure_scope, width=20, state=tk.DISABLED)
        self.setup_btn.pack(side=tk.LEFT, padx=20)
        
        # Acquisition panel
        acq_frame = ttk.LabelFrame(self.root, text="Data Acquisition", padding="10")
        acq_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=5)
        
        ttk.Label(acq_frame, text="Start Segment:").pack(side=tk.LEFT, padx=5)
        self.start_seg_var = tk.IntVar(value=1)
        self.start_seg_spin = ttk.Spinbox(acq_frame, from_=1, to=10000, 
                                          textvariable=self.start_seg_var, width=10)
        self.start_seg_spin.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(acq_frame, text="Count:").pack(side=tk.LEFT, padx=(20, 5))
        self.count_var = tk.IntVar(value=10)
        self.count_spin = ttk.Spinbox(acq_frame, from_=1, to=1000, 
                                      textvariable=self.count_var, width=10)
        self.count_spin.pack(side=tk.LEFT, padx=5)
        
        self.capture_btn = ttk.Button(acq_frame, text="Capture New Data", 
                                      command=self.capture_new_data, width=15, state=tk.DISABLED)
        self.capture_btn.pack(side=tk.LEFT, padx=(15, 5))
        
        self.collect_btn = ttk.Button(acq_frame, text="Collect Segments", 
                                      command=self.collect_segments, width=15, state=tk.DISABLED)
        self.collect_btn.pack(side=tk.LEFT, padx=5)
        
        self.seg_info_label = ttk.Label(acq_frame, text="", font=("Arial", 9))
        self.seg_info_label.pack(side=tk.LEFT, padx=10)
        
        # Control panel
        control_frame = ttk.Frame(self.root, padding="10")
        control_frame.pack(side=tk.TOP, fill=tk.X)
        
        self.status_label = ttk.Label(control_frame, text="Connect to instrument to begin", font=("Arial", 12))
        self.status_label.pack(side=tk.LEFT, padx=5)
        
        self.info_label = ttk.Label(control_frame, text="", font=("Arial", 10))
        self.info_label.pack(side=tk.LEFT, padx=20)
        
        # Playback controls
        playback_frame = ttk.Frame(control_frame)
        playback_frame.pack(side=tk.RIGHT, padx=5)
        
        self.first_btn = ttk.Button(playback_frame, text="⏮ First", command=self.first_segment, width=10)
        self.first_btn.pack(side=tk.LEFT, padx=2)
        
        self.prev_btn = ttk.Button(playback_frame, text="◀ Prev", command=self.prev_segment, width=10)
        self.prev_btn.pack(side=tk.LEFT, padx=2)
        
        self.play_btn = ttk.Button(playback_frame, text="▶ Play", command=self.toggle_play, width=10)
        self.play_btn.pack(side=tk.LEFT, padx=2)
        
        self.next_btn = ttk.Button(playback_frame, text="Next ▶", command=self.next_segment, width=10)
        self.next_btn.pack(side=tk.LEFT, padx=2)
        
        self.last_btn = ttk.Button(playback_frame, text="Last ⏭", command=self.last_segment, width=10)
        self.last_btn.pack(side=tk.LEFT, padx=2)
        
        # Speed control
        speed_frame = ttk.Frame(control_frame)
        speed_frame.pack(side=tk.RIGHT, padx=10)
        
        ttk.Label(speed_frame, text="Speed (ms):").pack(side=tk.LEFT, padx=2)
        self.speed_var = tk.IntVar(value=self.play_speed)
        self.speed_spin = ttk.Spinbox(speed_frame, from_=100, to=2000, increment=100, 
                                      textvariable=self.speed_var, width=8,
                                      command=self.update_speed)
        self.speed_spin.pack(side=tk.LEFT, padx=2)
        
        # Matplotlib figure
        self.fig, self.ax = plt.subplots(figsize=(13, 5))
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.root)
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        
        self._set_button_state(tk.DISABLED)
    
    def _set_button_state(self, state):
        self.first_btn.config(state=state)
        self.prev_btn.config(state=state)
        self.play_btn.config(state=state)
        self.next_btn.config(state=state)
        self.last_btn.config(state=state)
    
    def connect_scope(self):
        """Connect to the oscilloscope"""
        def connect():
            try:
                self.status_label.config(text="Connecting...")
                resource = self.ip_var.get()
                idn = get_instrument_id(resource)
                self.root.after(0, lambda: self._connected(resource, idn))
            except Exception as e:
                self.root.after(0, lambda: self._connect_error(str(e)))
        
        self.connect_btn.config(state=tk.DISABLED)
        thread = threading.Thread(target=connect, daemon=True)
        thread.start()
    
    def _connected(self, resource, idn):
        """Called when connection succeeds"""
        self.visa_resource = resource
        self.connected = True
        self.idn_label.config(text=f"✓ {idn}", foreground="green")
        self.status_label.config(text="Connected - Ready to configure")
        self.connect_btn.config(state=tk.NORMAL, text="Reconnect")
        self.setup_btn.config(state=tk.NORMAL)
        self.capture_btn.config(state=tk.NORMAL)
        self.collect_btn.config(state=tk.NORMAL)
    
    def _connect_error(self, error_msg):
        """Called when connection fails"""
        self.status_label.config(text=f"Connection failed: {error_msg}")
        self.idn_label.config(text="Connection failed", foreground="red")
        self.connect_btn.config(state=tk.NORMAL)
    
    def configure_scope(self):
        """Configure scope with setup parameters"""
        def setup():
            try:
                self.root.after(0, lambda: self.status_label.config(text="Configuring scope..."))
                
                setup_scope_acquisition(
                    self.visa_resource,
                    channel_scale=self.ch_scale_var.get(),
                    timebase_scale=self.tb_scale_var.get(),
                    trigger_level=self.trig_level_var.get(),
                    timebase_position=self.tb_pos_var.get(),
                    sample_rate=self.srate_var.get(),
                    acquire_points=self.acq_pts_var.get(),
                    segment_count=self.seg_count_var.get()
                )
                
                self.root.after(0, lambda: self.status_label.config(text="Scope configured - Ready to capture"))
                self.root.after(0, lambda: self.setup_btn.config(state=tk.NORMAL))
            except Exception as e:
                self.root.after(0, lambda: self.status_label.config(text=f"Setup error: {str(e)}"))
                self.root.after(0, lambda: self.setup_btn.config(state=tk.NORMAL))
        
        self.setup_btn.config(state=tk.DISABLED)
        thread = threading.Thread(target=setup, daemon=True)
        thread.start()
    
    def capture_new_data(self):
        """Trigger single acquisition on scope"""
        def capture():
            try:
                self.root.after(0, lambda: self.status_label.config(text="Triggering :SINGle acquisition..."))
                trigger_single_acquisition(self.visa_resource)
                self.root.after(0, lambda: self.status_label.config(text="Acquisition triggered - waiting for trigger event"))
            except Exception as e:
                self.root.after(0, lambda: self.status_label.config(text=f"Capture error: {str(e)}"))
                self.root.after(0, lambda: self.capture_btn.config(state=tk.NORMAL))
                return
            self.root.after(0, lambda: self.capture_btn.config(state=tk.NORMAL))
        
        self.capture_btn.config(state=tk.DISABLED)
        thread = threading.Thread(target=capture, daemon=True)
        thread.start()
    
    def collect_segments(self):
        """Collect segments from scope in background thread"""
        def collect():
            try:
                start = self.start_seg_var.get()
                count = self.count_var.get()
                self.root.after(0, lambda: self.status_label.config(
                    text=f"Downloading segments {start} to {start+count-1}..."
                ))
                
                segs, total = extract_segments_mode_a(
                    self.visa_resource, 
                    source="CHANnel1",
                    start_segment=start,
                    num_segments=count
                )
                self.root.after(0, lambda: self._data_loaded(segs, total))
            except Exception as e:
                self.root.after(0, lambda: self._load_error(str(e)))
        
        self.collect_btn.config(state=tk.DISABLED)
        self._set_button_state(tk.DISABLED)
        thread = threading.Thread(target=collect, daemon=True)
        thread.start()
    
    def _data_loaded(self, segments, total_available):
        """Called when data is loaded"""
        self.segments = segments
        self.total_segments_available = total_available
        self.status_label.config(text=f"Loaded {len(self.segments)} segments")
        self.seg_info_label.config(text=f"(Total available on scope: {total_available})")
        self.collect_btn.config(state=tk.NORMAL)
        self._set_button_state(tk.NORMAL)
        self.plot_segment(0)
    
    def _load_error(self, error_msg):
        """Called when loading fails"""
        self.status_label.config(text=f"Error: {error_msg}")
        self.collect_btn.config(state=tk.NORMAL)
        self.ax.clear()
        self.ax.text(0.5, 0.5, f"Failed to load data:\n{error_msg}", 
                    ha='center', va='center', transform=self.ax.transAxes, fontsize=12)
        self.canvas.draw()
    
    def plot_segment(self, index):
        """Plot a specific segment"""
        if not self.segments or index < 0 or index >= len(self.segments):
            return
        
        self.current_index = index
        seg = self.segments[index]
        
        self.ax.clear()
        self.ax.plot(seg['t_s'] * 1e9, seg['y_raw'], linewidth=1)
        
        self.ax.set_xlabel('Time (ns)', fontsize=12)
        self.ax.set_ylabel('ADC Value (raw)', fontsize=12)
        self.ax.set_title(f"Segment {seg['index']} | Time Tag: {seg['ttag_s']*1e6:.3f} µs", 
                         fontsize=14, fontweight='bold')
        self.ax.grid(True, alpha=0.3)
        
        self.info_label.config(
            text=f"Segment {index + 1}/{len(self.segments)} | Points: {len(seg['y_raw'])}"
        )
        
        self.canvas.draw()
    
    def first_segment(self):
        self.plot_segment(0)
    
    def last_segment(self):
        self.plot_segment(len(self.segments) - 1)
    
    def prev_segment(self):
        if self.current_index > 0:
            self.plot_segment(self.current_index - 1)
    
    def next_segment(self):
        if self.current_index < len(self.segments) - 1:
            self.plot_segment(self.current_index + 1)
    
    def toggle_play(self):
        self.is_playing = not self.is_playing
        if self.is_playing:
            self.play_btn.config(text="⏸ Pause")
            self._play_next()
        else:
            self.play_btn.config(text="▶ Play")
    
    def _play_next(self):
        if not self.is_playing:
            return
        
        if self.current_index < len(self.segments) - 1:
            self.next_segment()
            self.root.after(self.play_speed, self._play_next)
        else:
            self.is_playing = False
            self.play_btn.config(text="▶ Play")
    
    def update_speed(self):
        self.play_speed = self.speed_var.get()


def main():
    root = tk.Tk()
    app = ScopeSetupAndViewerGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
