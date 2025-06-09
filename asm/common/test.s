.section .rodata

EXIT_SYSCALL:
    .quad 60
EXIT_STATUS:
    .quad 0

.section .data

ARR:
    .byte 17
    .byte 99

.section .text

.global _start

_start:
    mov $ARR, %rdx
    mov $2, %rcx
    call print_bytes_array

    mov EXIT_SYSCALL, %rax
    mov EXIT_STATUS, %rdi
    syscall
