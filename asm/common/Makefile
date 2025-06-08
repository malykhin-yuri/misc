print.o:
	as -g print.s -o print.o

test.o:
	as -g test.s -o test.o

test: test.o print.o
	ld -g test.o print.o -o test.bin

all: test

clean:
	rm -f test.o print.o test.bin
