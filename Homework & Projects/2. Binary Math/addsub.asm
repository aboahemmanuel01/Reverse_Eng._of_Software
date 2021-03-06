; nasm -f elf64 addsub.asm && gcc -static -o addsub addsub.o

; This program uses the Linux sys_write system call.  See the table located here:
; https://blog.rchapman.org/posts/Linux_System_Call_Table_for_x86_64/

	global main
	extern puts
	extern atol

	section .text

main:	;mov rdi, 0xff00f043210099aa
	;call write_binary_qword
	
	push rbp
	mov rbp,rsp
	cmp rdi,3
	je fine
	
	mov rdi, eargs
	call puts
	mov rax,1
	jmp done

fine:  
	sub rsp, 16
	push rsi
	mov rdi, [rsi+8]
	call atol
	mov [rbp-8], rax

	pop rdi
	mov rdi, [rdi+16]
	call atol
	mov [rbp-16], rax 

	; Perform Addition
        mov rdi, add
        call puts
        mov rdi, [rbp-8]        
        call write_binary_qword 
        call write_endl

        mov rdi, [rbp-16]      
        call write_binary_qword 
        call write_endl

        mov rdi, [rbp-8]        
        add rdi, [rbp-16]    
        call write_binary_qword 
        call write_endl
	
	; Perform subtraction
        mov rdi, sub
        call puts
        mov rdi, [rbp-8]        
        call write_binary_qword 
        call write_endl

        mov rdi, [rbp-16]       
        call write_binary_qword 
        call write_endl

        mov rdi, [rbp-8]       
        sub rdi, [rbp-16]       
        call write_binary_qword 
        call write_endl

	mov rax, 0
	jmp done

write_binary_qword:
	push rbp
	mov rbp, rsp
	; Store rdi on the stack.  At this point rdi is occupying
	; the following addresses: rbp-1 through rbp-8.
	push rdi
	mov rcx, 8
	; Zero out rax.  While assigning to eax would zero the high
	; bits of rax, assigning to ah or al will not.
.top:	mov rax, 0
	; Get the next byte to print.  We have arranged to get them
	; in order from highest order to lowest (big endian).
	mov al, BYTE [rbp+rcx-9]
	; Save important data.
	push rcx
	push rax
	; Get high nybble and divide by four.
	and rax, 0xf0
	shr rax, 2
	mov rdi, 1
	lea rsi, [nyb + rax]
	mov rdx, 4
	mov rax, 1
	syscall
	call write_space
	; Restore the byte value.
	pop rax
	; Get low nybble and multiply by four.
	and rax, 0xf
	shl rax, 2
	mov rdi, 1
	lea rsi, [nyb + rax]
	mov rdx, 4
	mov rax, 1
	syscall
	call write_space
	; Restore the index.
	pop rcx
	loop .top
	leave
	ret

write_space:
	mov rdi, 1
	mov rsi, space
	mov rdx, 1
	mov rax, 1
	syscall
	ret

write_endl:
	mov rdi, 1
	mov rsi, endl
	mov rdx, 1
	mov rax, 1
	syscall
	ret

done:	
	leave
	ret

	section .data
nyb:	db "0000"
	db "0001"
	db "0010"
	db "0011"
	db "0100"
	db "0101"
	db "0110"
	db "0111"
	db "1000"
	db "1001"
	db "1010"
	db "1011"
	db "1100"
	db "1101"
	db "1110"
	db "1111"
add: db "Adding:",10,0
sub: db "Subtracting:",10,0
eargs: db "Expected exactly two integer arguments.", 0
space: db " "
endl:	db 10,0
