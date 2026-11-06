/* Minimal BIOS boot-sector test. This is not Kali and contains no Linux tools. */
.code16
.global _start
_start:
    cli
    xor %ax,%ax
    mov %ax,%ds
    mov %ax,%ss
    mov $0x7c00,%sp
    sti
    mov $message,%si
next:
    lodsb
    test %al,%al
    jz done
    mov $0x0e,%ah
    mov $0x07,%bx
    int $0x10
    jmp next
done:
    hlt
    jmp done
message: .asciz "QEMU guest boot verified - NOT Kali"
.org 510
.word 0xaa55
