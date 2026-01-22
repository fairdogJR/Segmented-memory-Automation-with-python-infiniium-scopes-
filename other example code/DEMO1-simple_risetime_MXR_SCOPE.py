# NOTE: the default pyvisa import works well for Python 3.6+
# if you are working with python version lower than 3.6, use 'import visa' instead of import pyvisa as visa

#HSDS 2025 Examples Tim Fairfield
#MXR Scope , source should be 5GB/sec(bert or pattern gen)
# This script demonstrates how to set up a Keysight MXR608B Infiniium oscilloscope using PyVISA

import pyvisa as visa
import time

def main():
    rm = visa.ResourceManager()
    scope = rm.open_resource('TCPIP0::192.168.50.126::hislip0::INSTR')
    scope.timeout = 40000

    print("Setting up oscilloscope...")
    try:
        scope.write('*RST')
        scope.write(':CHANnel1:INPut DC50')
        scope.write(':CHANnel2:INPut DC50')
        scope.write(':CHANnel1:DISPlay ON')
        scope.write(':CHANnel2:DISPlay ON')
        scope.write(':CHANnel3:DISPlay OFF')
        scope.write(':CHANnel4:DISPlay OFF')
        scope.write(':CHANnel5:DISPlay OFF')
        scope.write(':CHANnel6:DISPlay OFF')
        scope.write(':CHANnel7:DISPlay OFF')
        scope.write(':CHANnel8:DISPlay OFF')
        scope.write(':AUToscale')
        scope.query('*OPC?')
        scope.write(':CHANnel1:SCALe 0.2')
        scope.write(':CHANnel2:SCALe 0.2')
        scope.write(':ACQuire:POINts:ANALog 5000')
        scope.write(':TIMebase:SCALe 1e-08')
        scope.write(':MEASure:RISetime CHANnel1')
        scope.write(':MARKer:MODE MEASurement')
        print("Oscilloscope setup complete.\n")
    except Exception as e:
        print(f"Setup failed: {e}")
        scope.close()
        rm.close()
        return

    try:
        while True:
            input("Press Enter to acquire SINGLE and print results (Ctrl+C to exit)...")
            scope.write(':SINGle')
            time.sleep(1)  # Wait for acquisition to complete
            results = scope.query(':MEASure:RESults?').strip()
            results_list = [x.strip() for x in results.split(',')]
            display = (
                f"Current: {results_list}\n"
                # f"Current: {results_list[0]}\n"
                # f"Min: {results_list[1]}\n"
                # f"Max: {results_list[2]}\n"
                # f"Points: {results_list[3]}\n"
                + "-"*60
            )
            print(display)
    except KeyboardInterrupt:
        print("\nExiting...")
    finally:
        scope.close()
        rm.close()

if __name__ == "__main__":
    main()
