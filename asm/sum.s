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

curr_index:
    .quad 0
end_index:
    .quad 0
curr_num: /* curr number being read */
    .quad 0
curr_sum:
    .quad 0
output_index:
    .byte 0

.section .bss

.equ BUFFER_SIZE, 1024
.lcomm INPUT_BUFFER, BUFFER_SIZE
.equ OUTPUT_MAX_SIZE, 50
.lcomm OUTPUT_BUFFER, OUTPUT_MAX_SIZE

.section .text

.global _start

_start:

main_read_loop:
    movq $0, curr_index

    movq $SYS_READ, %rax
    movq $STDIN, %rdi
    movq $INPUT_BUFFER, %rsi
    movq $BUFFER_SIZE, %rdx
    syscall

/* TODO: do not assume space before eof */
    movq %rax, end_index
    cmpq $0, %rax
    je finish

process_char_loop:
    movq curr_index, %rdi

    cmpq %rdi, end_index
    je main_read_loop

    movzx INPUT_BUFFER(,%rdi,1), %rax
    incq %rdi
    movq %rdi, curr_index

    cmpq $ASCII_SPACE, %rax
    je add_number
    cmpq $ASCII_NEWLINE, %rax
    je finish

    subq $ASCII_ZERO, %rax
    movq curr_num, %rbx
    imulq $10, %rbx
    addq %rax, %rbx
    movq %rbx, curr_num
    
    jmp process_char_loop

add_number:
    movq curr_sum, %rax
    addq curr_num, %rax
    movq %rax, curr_sum
    movq $0, curr_num
    jmp process_char_loop

finish:
/*
    output &curr_sum and exit

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
    movq curr_sum, %rax
    movq $10, %rcx
    divq %rcx /* quotient -> %rax, remainder -> %rdx */ 

    movq %rax, curr_sum
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
