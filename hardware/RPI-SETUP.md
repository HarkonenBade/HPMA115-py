For standard RPi mounting, the HPMA115 module is connected to the UART0 of the RPi on header pins 8 and 10. The unit is fed power from header pin 2, 6 and 9.

The UART can be accessed in a standard raspbian install as `/dev/ttyS0`, this may need to be enabled, if so invoke `sudo raspi-config`, go to `3 Interface` followed by `I6 Serial`. Then choose 'no' the linux console should not be on the serial port, and 'yes' the serial port hardware should be enabled. Then reboot the device. 
