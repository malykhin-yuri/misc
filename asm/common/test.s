.section .data

EXIT_SYSCALL:
    .quad 60
EXIT_STATUS:
    .quad 0

CHAR:
    .byte 89 /* "Y" */
    .byte 117 /* "u" */
    .byte 114 /* "r" */
    .byte 97 /* "a" */
    .byte 33 /* "!" */
    .byte 10 /* "\n" */

.section .text


.global _start

_start:
    mov $CHAR, %rdx
    mov $6, %rcx
    call print_char_array

/* exit syscall; arg = exit status */
    mov EXIT_SYSCALL, %rax
    mov EXIT_STATUS, %rdi
    syscall
