from sys import argv
from util import *
import os.path
import struct

import parser
import dat

def main():
    filename = argv[1]
    output = argv[2]
    for check in [".obj", ".obj.po.out", ".dat"]:
        if not os.path.exists(filename + check):
            print("%s does not exist!" % filename + check)
            return
    with open(filename + ".obj", "rb") as fin:
        d = dat.DatParser(filename + ".dat")
        cur = ""
        strings = []
        for line in open(filename + ".obj.po.out", "r", encoding="utf-8").readlines():
            if line[-1] == "\x0a":
                line = line[:-1]
            if line == "":
                strings.append(cur[:-1])
                cur = ""
            else:
                cur += line + "\n"
        if cur != "":
            strings.append(cur[:-1])
        #print(strings)
        #return
        blocks = []
        tail = []
        cnt = uint32(fin)
        pos = 0
        header = fin.read(0x2c)
        cur = 0
        xpos = 0
        while True:
            if fin.read(1) == b"":
                break
            else:
                fin.seek(-1, 1)
            size = uint32(fin)
            t = uint16(fin)
            tmp = None
            if t == 0x64:
                tmp = parser.x64(fin.read(size - 6), pos, cnt, d, xpos)
                if cur < len(strings):
                    tmp.string = strings[cur]
                cur += 1
                if tmp.magic != b"\xff" * 4:
                    xpos += 1
            elif t == 0x68:
                tmp = parser.x68(fin.read(size - 6), pos, cnt, d, xpos)
                if cur < len(strings):
                    tmp.string = strings[cur]
                cur += 1
                if tmp.magic != b"\xff" * 4:
                    xpos += 1
            elif t == 0x67:
                tmp = parser.x67(fin.read(size - 6))
                for x in range(tmp.cnt):
                    if cur < len(strings):
                        tmp.strings[x] = strings[cur]
                    cur += 1
            elif t == 0x12e:
                tmp = parser.x2e01(fin.read(size - 6))
                if cur < len(strings):
                    tmp.string = strings[cur]
                cur += 1
            elif t == 0x323:
                tmp = parser.x2303(fin.read(size - 6))
                for x in range(tmp.cnt + 1):
                    if cur < len(strings):
                        tmp.strings[x] = strings[cur]
                    cur += 1
            else:
                blocks.append(parser.Block(t, fin.read(size - 6)))

            if tmp is not None:
                current, end = tmp.write()
                blocks.append(current)
                cnt += len(end)
                tail += end
            pos += 1

        fout = open(output + ".obj", "wb")
        write_u32(len(blocks) + len(tail), fout)
        fout.write(header)
        for b in blocks + tail:
            fout.write(b.write())
        fout.close()

        print("replaced %d lines" % cur)

        x = 0
        while True:
            if x >= len(d.blocks):
                break
            if d.blocks[x] == "":
                del d.blocks[x]
            else:
                x += 1
        d.write(output + ".dat")

if len(argv) != 3:
    print("Usage: repack.py file output")
else:
    main()
