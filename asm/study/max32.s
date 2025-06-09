/*
 * Find the maximum. 32-bit version.
 * 
 * %edi - index of the data item
 * %ebx - largest item found
 * %eax - current item
 */

    .section .data

data_items:
    .long 5,77,81,9,101,5,0 /* zero-terminated */

    .section .text

    .globl _start

_start:
    movl $0, %edi
    movl data_items(,%edi,4), %eax
    movl %eax, %ebx

start_loop:
    cmpl $0, %eax
    je loop_exit
    incl %edi
    movl data_items(,%edi,4), %eax
    cmpl %ebx, %eax
    jle start_loop
    movl %eax, %ebx
    jmp start_loop

loop_exit:
    movl $1, %eax
    /* %ebx = result = exit status */
    int $0x80
