import sys
import shutil
import struct

if len(sys.argv) != 4:
	print("Usage: patch-eboot.py SOURCE.BIN number OUTPUT.BIN")
	sys.exit()

input = sys.argv[1]
number = int(sys.argv[2])
output = sys.argv[3]

shutil.copyfile(input, output)

fout = open(output, "r+b")
# in "stock" voice.afs there are 0x535f (21343) entries
# to be able to use more we should patch original eboot in two places
# both entries look like this:
# 5f 53 07 24
# which actually is
# li $a3, 0x535F
# first one is at 0x644f0 and the second one is at 0x8995c
def patch(fout, offset, number):
	fout.seek(offset, 0)
	if fout.read(2) != b"\x5f\x53":
		# something is wrong, different/encrypted eboot?
		sys.exit(1)
	fout.seek(offset, 0)
	fout.write(struct.pack("<H", number))

patch(fout, 0x644f0, number)
patch(fout, 0x8995c, number)

fout.close()
