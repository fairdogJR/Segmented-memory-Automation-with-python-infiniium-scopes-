# NOTE: the default pyvisa import works well for Python 3.6+
# if you are working with python version lower than 3.6, use 'import visa' instead of import pyvisa as visa

import pyvisa as visa
import time
# start of Untitled

#this is the Most reliable way to ensure the M8070B is not in BUSY state 
# before proceeding with any command that causes an intrument busy condition
#
def wait_for_dataout1_ready(instr, timeout=30):
    #return # exit early to demo no wait for M8070B to be ready
    #"""Polls :STATus:INSTrument:RUN? 'M1.DataOut1' until it returns 1 or timeout (seconds) is reached."""
    import time
    start_time = time.time()
    while True:
        status = int(instr.query(':STATus:INSTrument:RUN? "M1.DataOut1"').strip())
        print(f"Polling DataOut1 ready status: {status}")
        if status == 1:
            print("Instrument is ready.")
            break
        if (time.time() - start_time) > timeout:
            print("Timeout waiting for M1.DataOut1 to be ready.")
            break
        time.sleep(0.5)
    #print("skipping wait process")
rm = visa.ResourceManager()
print("Resource manager created.")

M8070B = rm.open_resource('TCPIP0::192.168.50.109::hislip0::INSTR')
print("Connected to M8070B instrument.")

M8070B.timeout = 40000
print("Timeout set to 40000 ms.")

idn = M8070B.query('*IDN?')
print(f"Instrument ID: {idn}")


# ;:STATus:INSTrument:RUN:WAIT? 'M1.DataOut1';:STATus:INSTrument:RUN:WAIT? 'M1.DataOut2'
#  ensures the BERT is finished its process. It is similar to an *opc? command in behaviour but is specific to this instrument series.
print("Instrument reset with *RST and wait for DataOut1 and DataOut2 to finish.")
M8070B.write("*RST;")
wait_for_dataout1_ready(M8070B)
print("Instrument reset complete.") 

temp_values = M8070B.query_ascii_values(':SOURce:FREQuency? \"%s\"' % ('M1.ClkGen'))
frequency = temp_values[0]
print(f"Clock generator frequency after preset: {frequency}")

temp_values = M8070B.query_ascii_values(':OUTPut:STATe? \"%s\"' % ('M1.DataOut1'))
state = int(temp_values[0])
print(f"Data output 1 state: {state}")

print("Set the clock generator frequency to 4.5 GHz and waited for DataOut1 and DataOut2 to finish.")
M8070B.write(":SOURce:FREQuency 'M1.ClkGen',4500000000" )
wait_for_dataout1_ready(M8070B)

print("Reset and wait until not busy before proceeding.")
M8070B.write("*RST")
wait_for_dataout1_ready(M8070B)

print("Set the clock generator frequency to 3.5 GHz and waited for DataOut1 and DataOut2 to finish.")
M8070B.write(":SOURce:FREQuency 'M1.ClkGen',3500000000" )
wait_for_dataout1_ready(M8070B)

print("Set the interference state to random for DataOut1 and waited for it to be ready.")
M8070B.write(":SOURce:INTerference:RANDom:STATe 'M3.DataOut1',1;")
wait_for_dataout1_ready(M8070B)

M8070B.close()
print("M8070B connection closed.")

rm.close()
print("Resource manager closed.")

# end of Untitled
