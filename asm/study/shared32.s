    .section .data

hello_message:
    .asciz "hello world!!!\n"

    .section .text
    .global _start

_start:
    push $hello_message
    call printf

    push $0
    call exit
