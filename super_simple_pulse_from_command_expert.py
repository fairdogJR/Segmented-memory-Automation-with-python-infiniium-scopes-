# NOTE: the default pyvisa import works well for Python 3.6+
# if you are working with python version lower than 3.6, use 'import visa' instead of import pyvisa as visa

import pyvisa as visa
import time
# start of Untitled

rm = visa.ResourceManager()
infiniium = rm.open_resource('TCPIP0::192.168.0.2::hislip0::INSTR')
infiniium.timeout = 20000
#infiniium.write('*RST')
idn = infiniium.query('*IDN?')

infiniium.write(':CHANnel1:SCALe %G' % (0.2))
infiniium.write(':TIMebase:SCALe %G' % (2e-08))
infiniium.write(':TRIGger:LEVel %s,%G' % ('CHANNEL1', 0.32))
infiniium.write(':TIMebase:POSition %G' % (4e-08))
infiniium.write(':TIMebase:POSition %G' % (0.0))

infiniium.write(':ACQuire:MODE %s' % ('SEGMented'))
infiniium.write(':ACQuire:SRATe:ANALog %s' % ('MAX'))
infiniium.write(':ACQuire:POINts:ANALog %d' % (1500))
infiniium.write(':ACQuire:SEGMented:COUNt %d' % (65536))
infiniium.write(':SINGle')
infiniium.close()
rm.close()

# end of Untitled
