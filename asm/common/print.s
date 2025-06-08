.section .data

/*
WRITE_SYSCALL: .byte 1
STDOUT_FD: .byte 1
*/

.section .text

.global print_array

print_array:
/* print array of bytes to stdout
    call convention:
 * arg 1: mem first location (%rax)
 * arg 2: mem after last location (%rbx)
 * clobbers: ...
 */

    /* syscall clobbers rcx, so save it */
    mov %rcx, %r15
    call write_byte

    mov %rbx, %rax
    call write_byte

    mov %r15, %rax
    call write_byte

    ret

write_byte:
/* byte <- %rax */
    mov %rax, %rsi  /* message */
    mov $1, %rax    /* syscall no */
    mov $1, %rdi    /* fd */
    mov $1, %rdx    /* len */
    syscall
    ret
