#!/bin/sh

qemu-system-arm -M stm32vldiscovery -m 128K -no-reboot -nographic -monitor telnet:127.0.0.1:1234,server,nowait -kernel start.bin
