# dat parser!
# http://toradora.xyz.is/wiki/.dat_file_format

# usage:
#	x = DatParser("_0010ESS0.dat")
# change some stuff in x.blocks
#	x.save("newfile.dat")

import math
import struct

from util import *

def up(x):
	return math.ceil(x / 0x800) * 0x800

def align(t):
	return t + b"\x00" * (up(len(t)) - len(t))

class DatParser():
	header = b"\x47\x50\x44\x41" # GPDA
	blocks = []

	def __init__(self, path):
		with open(path, "rb") as fin:
			fin.seek(12, 1)
			cnt = uint32(fin)
			entries = []
			for x in range(cnt):
				start = uint32(fin)
				fin.seek(4, 1)
				length = uint32(fin)
				fin.seek(4, 1)
				entries.append((start, length))

			for start, length in entries:
				fin.seek(start, 0)
				self.blocks.append(fin.read(length).decode("ascii"))

	def write(self, path):
		with open(path, "wb") as fout:
			header = self.header
			header += b"\x00" * 8
			header += struct.pack("<I", len(self.blocks))

			header_size = up(len(header) + 16 * len(self.blocks))
			prev = header_size

			# header table
			for block in self.blocks:
				header += struct.pack("<I", prev) + b"\x00" * 4 + struct.pack("<I", len(block)) + b"\x00" * 4
				prev += up(len(block))

			header = align(header)

			# actual data
			data = b""
			for block in self.blocks:
				data += align(block.encode("ascii"))

			header = header[:4] + struct.pack("<I", len(header) + len(data)) + header[8:]

			fout.write(header + data)
