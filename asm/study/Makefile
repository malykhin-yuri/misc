max32.o: max32.s
	as max32.s -o max32.o

max32: max32.o
	ld max32.o -o max32

pow32.o: pow32.s
	as --32 pow32.s -o pow32.o

pow32: pow32.o
	ld -m elf_i386 pow32.o -o pow32

factorial32.o: factorial32.s
	as -g --32 factorial32.s -o factorial32.o

factorial32: factorial32.o
	ld -g -m elf_i386 factorial32.o -o factorial32

shared32.o: shared32.s
	as -g --32 shared32.s -o shared32.o

# 32-bit linker requires: sudo apt install lib32z1 ?? TODO: figure out what deps were required
# 32-bit libc requires: sudo apt install gcc-multilib
shared32: shared32.o
	ld -g -m elf_i386 --dynamic-linker /usr/lib32/ld-linux.so.2 shared32.o -lc -o shared32

clean:
	rm -f *.o max32 pow32 factorial32
