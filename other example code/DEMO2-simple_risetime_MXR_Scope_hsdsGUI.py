# NOTE: the default pyvisa import works well for Python 3.6+
# if you are working with python version lower than 3.6, use 'import visa' instead of import pyvisa as visa

#HSDS 2025 Examples Tim Fairfield
#MXR Scope , source should be 5GB/sec(bert or pattern gen)
# This script demonstrates how to set up a Keysight MXR608B Infiniium oscilloscope using PyVISA

import pyvisa as visa
import time
import tkinter as tk
from tkinter import ttk

class MXRGuiApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Keysight MXR Risetime Measurement")
        self.geometry("500x300")

        # GUI widgets
        self.results_label = ttk.Label(self, text="Results (Risetime, Stdev, Count, Points):")
        self.results_label.pack()

        self.results_text = tk.Text(self, height=10, width=60, wrap="none", font=("Consolas", 10))
        self.results_text.pack(pady=5)
        self.results_text.config(state=tk.DISABLED)

        # Acquire button (hidden until setup complete)
        self.button = ttk.Button(self, text="Acquire SINGLE & Update Results", command=self.acquire_and_update)
        self.button.pack(pady=10)
        self.button.pack_forget()  # Hide initially

        # VISA/Scope setup (run in after() to allow GUI to update)
        self.after(100, self.setup_scope)

        # Clean up on close
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def log_stage(self, message):
        self.results_text.config(state=tk.NORMAL)
        self.results_text.insert(tk.END, message + "\n")
        self.results_text.see(tk.END)
        self.results_text.config(state=tk.DISABLED)
        self.update_idletasks()

    def setup_scope(self):
        try:
            self.log_stage("Connecting to scope...")
            self.rm = visa.ResourceManager()
            self.scope = self.rm.open_resource('TCPIP0::192.168.50.126::hislip0::INSTR')
            self.scope.timeout = 40000

            self.log_stage("Resetting scope...")
            self.scope.write('*RST')
            self.log_stage("Setting channel inputs...")
            self.scope.write(':CHANnel1:INPut DC50')
            self.scope.write(':CHANnel2:INPut DC50')
            self.log_stage("Autoscale...")
            self.scope.write(':AUToscale')
            self.log_stage("Configuring channel display...")
            self.scope.write(':CHANnel1:DISPlay ON')
            self.scope.write(':CHANnel2:DISPlay OFF')
            self.log_stage("Setting channel scales...")
            self.scope.write(':CHANnel1:SCALe 0.1')
            self.scope.write(':CHANnel2:SCALe 0.1')
            self.log_stage("Setting acquisition points...")
            self.scope.write(':ACQuire:POINts:ANALog 5000')
            self.log_stage("Setting timebase scale...")
            self.scope.write(':TIMebase:SCALe 500e-12')
            self.log_stage("Setting up measurement...")
            self.scope.write(':MEASure:RISetime CHANnel1')
            self.scope.write(':MARKer:MODE MEASurement')
            self.log_stage("Running initial SINGLE acquisition...")
            self.scope.write(':SINGle')
            self.log_stage("Scope setup complete.\n")
            self.button.pack(pady=10)  # Show the button
        except Exception as e:
            self.log_stage(f"Setup failed: {e}")

    def acquire_and_update(self):
        self.scope.write(':SINGle')
        time.sleep(1)  # Wait for acquisition to complete
        results = self.scope.query(':MEASure:RESults?').strip()
        results_list = [x.strip() for x in results.split(',')]
        display = f"Risetime: {results_list[0]}\nStdev: {results_list[1]}\nCount: {results_list[2]}\nPoints: {results_list[3]}\n"
        self.results_text.config(state=tk.NORMAL)
        self.results_text.insert(tk.END, display)
        self.results_text.see(tk.END)
        self.results_text.config(state=tk.DISABLED)

    def on_close(self):
        try:
            self.scope.close()
            self.rm.close()
        except Exception:
            pass
        self.destroy()

if __name__ == "__main__":
    app = MXRGuiApp()
    app.mainloop()
