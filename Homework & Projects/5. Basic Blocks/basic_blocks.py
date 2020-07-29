#!/usr/bin/env python3
#

import sys
from capstone import *
from capstone.x86_const import *
from elftools.elf.elffile import ELFFile

# Convert from ELF tools to constants used by Capstone.
decoder_ring = {
	'EM_386': CS_ARCH_X86,
	'EM_X86_64': CS_ARCH_X86,
	'ELFCLASS32': CS_MODE_32,
	'ELFCLASS64': CS_MODE_64
}



def is_mem(oper):
	"""Provided with an operand, determine if it is a memory reference."""
	return oper.type == X86_OP_MEM

def is_imm(oper):
	"""Provided with an operand, determine if it is immediate."""
	return oper.type == X86_OP_IMM

def is_reg(oper):
	"""Provided with an operand, determine if it is a register."""
	return oper.type == X86_OP_REG

class AddressException(Exception):
	"""Address is out of bounds."""
	def __init__(self, address, offset, size):
		self.address = address
		self.offset = offset
		self.size = size

	def __str__(self):
		return "Address Out Of Bounds: 0x%x is not in [0x%x, 0x%x]" % (
			self.address, self.offset, self.offset+self.size
		)


class RAD:
	"""Provide a random access disassembler (RAD)."""
	def __init__(self, code, arch, bits, offset):
		"""Start disassembly of the provided code blob.

		Arguments:
			code -- The binary blob of the code.
			arch -- The architecture, as defined by Capstone.
			bits -- The bit width, as defined by Capstone.
			offset -- The code offset to use.
		"""
		# Set up options for disassembly of the text segment.
		self.md = Cs(arch, bits)
		self.md.skipdata = True
		self.md.detail = True
		self.code = code
		self.offset = offset
		self.size = len(code)

	def at(self, address):
		"""Try to disassemble and return the instruction starting at
		the given address.  Note that the address is relative to the
		offset provided at creation, and that an AddressException is
		thrown when the address is out of bounds (below the offset or
		above the offset plus the length of the binary blob).
		"""
		index = address - self.offset
		if index < 0 or index >= self.size:
			raise AddressException(address, self.offset, self.size)
		# The maximun length of an x86-64 instruction is 15 bytes.  You can
		# exceed this with prefix bytes and the like, but you will get an
		# "general protection" (GP) exception on the processor.  So don't do
		# that.
		return next(self.md.disasm(self.code[index:index+15], address, count=1))

	def in_range(self, address):
		"""Determine if an address is in range."""
		index = address - self.offset
		return index >= 0 and index < self.size


def main():
	"""Disassemble the file(s) specified on the command line."""
	for filename in sys.argv[1:]:
		print("%s:"%filename)
		with open(filename, "rb") as f:
			# Try to decode as ELF.
			try:
				elf = ELFFile(f)
			except:
				print("Could not parse the file as ELF; cannot continue.")
				exit()

			# Convert and check to see if we support the file.
			bits = decoder_ring.get(elf['e_ident']['EI_CLASS'], None)
			arch = decoder_ring.get(elf['e_machine'], None)
			if arch is None:
				print("Unsupported architecture %s" % elf['e_machine'])
				exit()
			if bits is None:
				print("Unsupported bit width %s" % elf['e_ident']['EI_CLASS'])
				exit()

			# Get the .text segment's data.
			section = elf.get_section_by_name('.text')
			if not section:
				print("No .text section found in file; file may be stripped or obfuscated.")
				exit()
			code = section.data()

			# Set up options for disassembly of the text segment.
			rad = RAD(code, arch, bits, elf.header.e_entry)
			key_list = [elf.header.e_entry]
			identified_blocks = set()
			
			# Begin basic block at this point
			bbs = set([elf.header.e_entry])
			while len(key_list) > 0:
				
				address = key_list.pop()
				if address in identified_blocks:
					continue
				else:
					identified_blocks.add(address)

				# Disassemble 
				try:
					i = rad.at(address)
				except AddressException:
					continue


				# Get the next address
				nextaddr = i.address + len(i.bytes)

				if i.group(2):
					if is_imm(i.operands[0]):
						key_list.append(i.operands[0].value.imm)
						bbs.add(i.operands[0].value.imm)
					key_list.append(nextaddr)

				elif i.group(1) or i.group(7):
					if i.mnemonic == "jmp":
						if is_imm(i.operands[0]):
							key_list.append(i.operands[0].value.imm)
							bbs.add(i.operands[0].value.imm)
					else:
						key_list.append(i.operands[0].value.imm)
						key_list.append(nextaddr)
						bbs.add(i.operands[0].value.imm)
						bbs.add(nextaddr)

				elif i.group(3) or i.group(5):
					pass

				elif i.group(4):
					key_list.append(nextaddr)

				elif i.group(6):
					pass

				else:
					key_list.append(nextaddr)

			# This section print the basic blocks.
			list(bbs).sort()
			for address in bbs:
				if not rad.in_range(address):
					continue

				print("\nblock at: 0x%x" % address)
				while address != None:

					# Disassemble 
					try:
						i = rad.at(address)
					except AddressException:
						address = None
						continue

					# continue disassembly
					nextaddr = i.address + len(i.bytes)
					print("  %s\t%s" % (i.mnemonic, i.op_str))
					address = None
					if i.group(2):
						address = nextaddr

					elif i.group(1) or i.group(7):
						if i.mnemonic == "jmp":
							if is_imm(i.operands[0]):
								print("next: %s" % i.op_str)
							else:
								print("next: unknown")
						else:
							print("true: %s" % i.op_str)
							print("false: 0x%x" % nextaddr)

					elif i.group(3) or i.group(5):
						print("next: unknown")

					elif i.group(4):
						address = nextaddr

					elif i.group(6):
						print("next: unknown")

					else:
						address = nextaddr

		print()

if __name__ == "__main__":
	main()
