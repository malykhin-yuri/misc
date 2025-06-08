.section .data

WRITE_SYSCALL:
    .quad 1
STDOUT_FD:
    .quad 1

.section .text

.global print_char_array

print_char_array:
/* print array of chars to stdout
 * %rdx: mem start location
 * %rcx: counter
 * clobbers them + syscall clobbering :(
 */

    mov %rdx, %r14 /* write_byte clobbers rdx */
    mov %rcx, %r15 /* syscall clobbers rcx, so save it */
loop:
    mov %r14, %rdx
    call write_byte
    dec %r15
    inc %r14
    cmp $1, %r15
    jge loop
    ret

write_byte:
/* byte <- %rdx */
    mov WRITE_SYSCALL, %rax    /* syscall no */
    mov STDOUT_FD, %rdi    /* fd */
    mov %rdx, %rsi  /* message */
    mov $1, %rdx    /* len */
    syscall
    ret
