Try to write code for cortex-m3 microcontrollers.
Use stm32vldiscovery debugging board.

# Hello world project

Loads constant 999 in register R7.
You can see it by running ./run-qemu.sh and then in another terminal:
$ telnet localhost 1234
$ (qemu) info registers

# References
А.В. Немоляев, ``GCC Cortex-M3''
