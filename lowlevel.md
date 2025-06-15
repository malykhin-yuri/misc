Some links on low-level programming

# Assembler

* Book "Programming from the ground up" by J. Bartlett. Programming basics with assembler on i386 GNU/Linux.
* Short i386 guide: https://flint.cs.yale.edu/cs421/papers/x86-asm/asm.html

# Linux Kernel

* https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/
* https://github.com/torvalds/linux

Useful files:
* x86_64 syscall ABI: https://github.com/torvalds/linux/blob/master/arch/x86/entry/entry_64.S
* syscall numbers: https://github.com/torvalds/linux/blob/master/arch/x86/entry/syscalls/syscall_64.tbl

# Toolchain
* gcc + gdb + binutils:
    * https://gcc.gnu.org/onlinedocs/
    * https://sourceware.org/gdb/current/onlinedocs/gdb.html/
    * https://sourceware.org/binutils/docs/

## Cross-compiling
``The build machine is the system which you are using, the host machine is the
system where you want to run the resulting compiler (normally the build
machine), and the target machine is the system for which you want the compiler
to generate code.''

Build gcc as explained in https://gcc.gnu.org/install :
$ sudo apt instal flex
$ cd /path/to/gcc-source
$ ./contrib/download_prerequisites
$ cd /path/to/gcc-build
$ /path/to/gcc-source/configure --host=x86_64-pc-linux-gnu --target arm-none-eabi --prefix /path/to/gcc-install

# C library

* glibc: https://sourceware.org/glibc/

# Microcontrollers

* https://en.wikipedia.org/wiki/Microcontroller
* https://en.wikipedia.org/wiki/Firmware
* reddit/embedded

## Arm

Download arm toolchain:
https://developer.arm.com/downloads/-/arm-gnu-toolchain-downloads
x86_64 linux hosted 
target: arm-none-eabi

# Examples

## Memory management
* https://stackoverflow.com/questions/71413587/why-is-malloc-considered-a-library-call-and-not-a-system-call
* man 3 malloc
* man 2 brk
