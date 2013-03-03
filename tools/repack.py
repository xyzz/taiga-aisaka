from sys import argv
from util import *
import os.path
import struct

import parser

def write_u32(x, fout):
    fout.write(struct.pack('<I', x))

def write_u16(x, fout):
    fout.write(struct.pack('<H', x))

def main():
    filename = argv[1]
    output = argv[2]
    if not os.path.exists(filename):
        print("%s does not exist!" % filename)
        return
    if not os.path.exists(filename + ".po.out"):
        print("%s.po.out does not exist!" % filename)
        return
    with open(filename, "rb") as fin:
        fout = open(output, "wb")
        strings = [line[:-1] if line[-1] == "\x0a" else line for line in open(filename + ".po.out", "r", encoding="utf-8").readlines()]
        fout.write(fin.read(0x30))
        cur = 0
        while True:
            if fin.read(1) == b"":
                break
            else:
                fin.seek(-1, 1)
            size = uint32(fin)
            t = uint16(fin)
            if t == 0x64:
                tmp = parser.x64(fin.read(size - 6))
                tmp.string = strings[cur]
                out = tmp.write()
                write_u32(len(out) + 6, fout)
                write_u16(0x64, fout)
                fout.write(out)

                #if cur == 1 and filename.find("0000ESS") != -1:
                #    write_u32(len(out) + 6, fout)
                #    write_u16(0x64, fout)
                #    fout.write(out)

                cur += 2
            elif t == 0x68:
                tmp = parser.x68(fin.read(size - 6))
                tmp.string = strings[cur]
                out = tmp.write()
                write_u32(len(out) + 6, fout)
                write_u16(0x68, fout)
                fout.write(out)

                cur += 2
            elif t == 0x67:
                tmp = parser.x67(fin.read(size - 6))
                for x in range(tmp.cnt):
                    tmp.strings[x] = strings[cur]
                    cur += 2
                out = tmp.write()
                write_u32(len(out) + 6, fout)
                write_u16(0x67, fout)
                fout.write(out)
            elif t == int("0x12e", 16):
                tmp = parser.x2e01(fin.read(size - 6))
                tmp.string = strings[cur]
                out = tmp.write()
                write_u32(len(out) + 6, fout)
                write_u16(int("0x12e", 16), fout)
                fout.write(out)

                cur += 2
            elif t == int("0x323", 16):
                tmp = parser.x2303(fin.read(size - 6))
                for x in range(tmp.cnt + 1):
                    tmp.strings[x] = strings[cur]
                    cur += 2
                out = tmp.write()
                write_u32(len(out) + 6, fout)
                write_u16(int("0x323", 16), fout)
                fout.write(out)
            else:
                fin.seek(-6, 1)
                fout.write(fin.read(size))
        fout.close()
        print("replaced %d lines" % cur)

if len(argv) != 3:
    print("Usage: unpack.py file.obj output.obj")
else:
    main()
