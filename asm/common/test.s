.section .data

EXIT_SYSCALL:
    .quad 60
EXIT_STATUS:
    .quad 0

CHAR:
    .byte 89 /* "Y" */
    .byte 33 /* "!" */
    .byte 10 /* "\n" */

.section .text


.global _start

_start:
    mov $CHAR, %rax
    mov $CHAR, %rbx
    mov $CHAR, %rcx
    inc %rbx
    inc %rcx
    inc %rcx
    call print_array

/* exit syscall; arg = exit status */
    /*
    mov $EXIT_SYSCALL, %rax
    mov $EXIT_STATUS, %rdi
    */
    mov EXIT_SYSCALL, %rax
    mov $0, %rdi
    syscall
