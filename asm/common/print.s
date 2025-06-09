.section .rodata

.equ SYS_WRITE, 1
.equ STDOUT_FD, 1
SEPARATOR:
    .ascii " "
NEWLINE:
    .ascii "\n"

.section .data

byte_buffer:
    .byte 0
digit_buffer:
    .byte 0

.section .text

.global print_bytes_array

print_bytes_array:
/* print array of bytes to stdout as digits
 * %rdx: mem start location
 * %rcx: counter
 * clobbers a lot of registers :(
 */
    mov %rdx, %r14 /* print_digit clobbers rdx */
    mov %rcx, %r15 /* syscall clobbers rcx */
loop:
    mov (%r14), %r13
    mov %r13, byte_buffer
    call print_byte
    call print_sep
    dec %r15
    inc %r14
    cmp $1, %r15
    jge loop

    call print_end
    ret

print_byte:
/* byte <- byte_buffer */
    xor %rax, %rax
    mov byte_buffer, %al
    mov $10, %bl
    div %bl /* quotient -> %al; remainder -> %ah */
    mov %al, byte_buffer
    add $48, %ah /* ascii code of symbol before '1' */
    mov %ah, digit_buffer
    call print_digit

    mov byte_buffer, %al
    cmp $1, %al
    jge print_byte
    ret

print_digit:
    mov $SYS_WRITE, %rax    /* syscall no */
    mov $STDOUT_FD, %rdi    /* fd */
    mov $digit_buffer, %rsi  /* message */
    mov $1, %rdx    /* len */
    syscall
    ret

print_sep:
    mov $SYS_WRITE, %rax    /* syscall no */
    mov $STDOUT_FD, %rdi    /* fd */
    mov $SEPARATOR, %rsi  /* message */
    mov $1, %rdx    /* len */
    syscall
    ret

print_end:
    mov $SYS_WRITE, %rax    /* syscall no */
    mov $STDOUT_FD, %rdi    /* fd */
    mov $NEWLINE, %rsi  /* message */
    mov $1, %rdx    /* len */
    syscall
    ret
