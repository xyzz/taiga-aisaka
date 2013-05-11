import struct

def uint32(fin):
    tmp = fin.read(4)
    return int(tmp[0]) + int(tmp[1]) * 256 + int(tmp[2]) * 256 ** 2 + int(tmp[3]) * 256 ** 3

def uint16(fin):
    tmp = fin.read(2)
    return int(tmp[0]) + int(tmp[1]) * 256

def write_u32(x, fout):
    fout.write(struct.pack('<I', x))

def write_u16(x, fout):
    fout.write(struct.pack('<H', x))
