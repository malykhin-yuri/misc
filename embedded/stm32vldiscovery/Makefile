CC = arm-none-eabi-gcc
CCFLAGS = -mthumb -mcpu=cortex-m3 -g
LD = arm-none-eabi-ld

start.bin: start.elf
	arm-none-eabi-objcopy -O binary start.elf start.bin

start.elf: start.o
	$(LD) -T l.ld start.o -o start.elf

start.o: start.s
	$(CC) $(CCFLAGS) -c -g -o start.o start.s
