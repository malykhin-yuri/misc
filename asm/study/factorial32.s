    .section .text

    .global _start
    .global factorial

_start:
    pushl $5
    call factorial
    addl $4, %esp

    movl %eax, %ebx
    movl $1, %eax
    int $0x80

    .type factorial, @function
factorial:
    pushl %ebp
    movl %esp, %ebp

    movl 8(%ebp), %eax
    cmpl $1, %eax
    je factorial_end
    decl %eax
    pushl %eax
    call factorial
    movl 8(%ebp), %ebx
    imull %ebx, %eax

factorial_end:
    movl %ebp, %esp
    popl %ebp
    ret
