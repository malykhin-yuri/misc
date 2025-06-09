/* Here we use C calling convention */

    .section .text

    .global _start

_start:
    pushl $3
    pushl $5
    call power
    addl $8, %esp
    movl %eax, %ebx /* result in exit code */

    movl $1, %eax
    int $0x80

    .type power, @function

power:
/* args: base, power (placed on the stack); returns in %eax
 * vars:
 *  %ebx - holds curr base
 *  %ecx - holds power
 */
    pushl %ebp
    movl %esp, %ebp
    subl $4, %esp /* for local var */

    movl 8(%ebp), %ebx
    movl 12(%ebp), %ecx

    movl %ebx, -4(%ebp) /* current result */
power_loop_start:
    cmpl $1, %ecx
    je power_end
    movl -4(%ebp), %eax
    imull %ebx, %eax
    movl %eax, -4(%ebp)
    decl %ecx
    jmp power_loop_start
power_end:
    movl -4(%ebp), %eax
    movl %ebp, %esp
    popl %ebp
    ret
