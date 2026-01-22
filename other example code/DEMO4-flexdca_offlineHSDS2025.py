# :SYSTem:DEFault
# :TIMebase:SCALe 2.0000E-10
# :SYSTem:AUToscale
# *OPC?
# :TIMebase:SCALe 1.0000E-10
# :MEASure:OSCilloscope:VAMPlitude
# :MEASure:OSCilloscope:VPP
# :MEASure:OSCilloscope:RISetime
# :MEASure:OSCilloscope:PERiod
# :MEASure:ANNotations:STATe ON
# :SYSTem:AUToscale
# *OPC?
# :TIMebase:SCALe 5.0000E-10

import pyvisa as visa
import time

# Connect to the FlexDCA (offline) at the specified VISA address
address = "TCPIP0::5CD3293ZXG::hislip0,4880::INSTR"
rm = visa.ResourceManager()
flexdca = rm.open_resource(address)
print(f"Connected to FlexDCA at {address}")
time.sleep(0.5)

# Reset instrument to default state
flexdca.write(":SYSTem:DEFault")
print("Instrument set to default state.")
time.sleep(0.5)

print("Loading simulation generator setup from file...")
flexdca.write(r':DISK:SETup:RECall "%USER_DATA_DIR%\Setups\HSDSDEMO7flexdca_complianceappSetup_2025-05-28_1.setx"')
flexdca.query("*OPC?")
time.sleep(0.5)

print("Switching instrument to Oscilloscope mode...")
flexdca.write(":SYSTem:MODE OSCilloscope")
print("Instrument is now in Oscilloscope mode.")

# Turn off Histogram1 display
flexdca.write(":HISTogram1:DISPlay OFF")
print("Histogram1 display turned OFF.")
time.sleep(0.5)


# Set the timebase scale to 200 ps/div
flexdca.write(":TIMebase:SCALe 2.0000E-10")
print("Timebase scale set to 200 ps/div.")
time.sleep(0.5)

# Autoscale the instrument
flexdca.write(":SYSTem:AUToscale")
print("Autoscale command sent.")
time.sleep(0.5)

# Wait for operation complete
flexdca.query("*OPC?")
print("Operation complete after autoscale.")
time.sleep(0.5)

# Set the timebase scale to 100 ps/div
flexdca.write(":TIMebase:SCALe 1.0000E-10")
print("Timebase scale set to 100 ps/div.")
time.sleep(0.5)

# Request vertical amplitude measurement
flexdca.write(":MEASure:OSCilloscope:VAMPlitude")
vampl = flexdca.query(":MEASure:OSCilloscope:VAMPlitude?")
print(f"Vertical Amplitude: {vampl.strip()}")
time.sleep(0.5)

# Request Vpp measurement
flexdca.write(":MEASure:OSCilloscope:VPP")
vpp = flexdca.query(":MEASure:OSCilloscope:VPP?")
print(f"Vpp: {vpp.strip()}")
time.sleep(0.5)

# Request Risetime measurement
flexdca.write(":MEASure:OSCilloscope:RISetime")
risetime = flexdca.query(":MEASure:OSCilloscope:RISetime?")
print(f"Risetime: {risetime.strip()}")
time.sleep(0.5)

# Request Period measurement
flexdca.write(":MEASure:OSCilloscope:PERiod")
period = flexdca.query(":MEASure:OSCilloscope:PERiod?")
print(f"Period: {period.strip()}")
time.sleep(0.5)

# Turn on measurement annotations
flexdca.write(":MEASure:ANNotations:STATe ON")
print("Measurement annotations turned ON.")
time.sleep(0.5)

# Autoscale again
flexdca.write(":SYSTem:AUToscale")
print("Autoscale command sent again.")
time.sleep(0.5)


# Wait for operation complete
flexdca.query("*OPC?")
print("Operation complete after second autoscale.")
time.sleep(0.5)

# Set the timebase scale to 500 ps/div
flexdca.write(":TIMebase:SCALe 5.0000E-10")
print("Timebase scale set to 500 ps/div.")
time.sleep(0.5)

# Trigger a single acquisition
flexdca.write(":ACQuire:SINGle")
print("Single acquisition triggered.")
flexdca.query("*OPC?")
print("Acquisition complete.")

print("Querying measurement results...")
results= flexdca.query(":measure:results?")
print(f"\n\n#########results{results.strip()}")

# Close the connection
flexdca.close()
rm.close()
print("FlexDCA session closed.")
