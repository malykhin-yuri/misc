.section .data

.equ SYS_EXIT, 60
.equ EXIT_STATUS, 0

ARR:
    .byte 17
    .byte 99

.section .text

.global _start

_start:
    mov $ARR, %rdx
    mov $2, %rcx
    call print_bytes_array

    mov $SYS_EXIT, %rax
    mov $EXIT_STATUS, %rdi
    syscall
