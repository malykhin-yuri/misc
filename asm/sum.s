/*
    Summator: read numbers from stdin, write sum to stdout
*/

.equ STDIN, 0
.equ STDOUT, 1

.equ SYS_READ, 0
.equ SYS_WRITE, 1
.equ SYS_EXIT, 60
.equ EXIT_STATUS, 0

.equ ASCII_SPACE, 32
.equ ASCII_NEWLINE, 10
.equ ASCII_ZERO, 48

.section .data

.section .bss

.equ BUFFER_SIZE, 1024
.lcomm INPUT_BUFFER, BUFFER_SIZE
.equ OUTPUT_MAX_SIZE, 50
.lcomm OUTPUT_BUFFER, OUTPUT_MAX_SIZE

.section .text

.global _start

_start:
/* registers:
 * %rbx - current number (callee-preserved in syscalls and C ABI)
 * %rdi - current read index
 * %rsi - end of read index
 * %r12 - current sum
 */
    movq $0, %rbx
    movq $0, %r12

main_read_loop:
    movq $SYS_READ, %rax
    movq $STDIN, %rdi
    movq $INPUT_BUFFER, %rsi
    movq $BUFFER_SIZE, %rdx
    syscall

    movq %rax, %rsi /* read count */
    cmpq $0, %rsi
    je finish

    movq $0, %rdi

process_char_loop:
    cmpq %rdi, %rsi
    je main_read_loop

    movzx INPUT_BUFFER(,%rdi,1), %rax
    incq %rdi

    cmpq $ASCII_SPACE, %rax
    je add_number
    cmpq $ASCII_NEWLINE, %rax
    je add_number

    subq $ASCII_ZERO, %rax
    imulq $10, %rbx
    addq %rax, %rbx
    
    jmp process_char_loop

add_number:
    call func_add_number
    jmp process_char_loop

func_add_number:
    addq %rbx, %r12
    movq $0, %rbx
    ret

finish:
    call func_add_number
/*
    output current sum and exit

    find digits of sum number:
    %rdi - addr of output start
    %r11 - output length
*/
    movq $OUTPUT_MAX_SIZE, %rdi
    movq $0, %r11

    decq %rdi
    movq $ASCII_NEWLINE, OUTPUT_BUFFER(,%rdi,1)
    incq %r11

store_digits_loop:
    movq $0, %rdx
    movq %r12, %rax
    movq $10, %rcx
    divq %rcx /* quotient -> %rax, remainder -> %rdx */ 

    movq %rax, %r12
    decq %rdi
    addq $ASCII_ZERO, %rdx
    movb %dl, OUTPUT_BUFFER(,%rdi,1)
    incq %r11

    cmpq $0, %rax
    jne store_digits_loop
output:
    movq $SYS_WRITE, %rax
    leaq OUTPUT_BUFFER(,%rdi,1), %rsi
    movq $STDOUT, %rdi
    movq %r11, %rdx /* length */
    syscall
exit:
    movq $SYS_EXIT, %rax
    movq $EXIT_STATUS, %rdi
    syscall
