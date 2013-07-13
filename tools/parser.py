import struct
import sys
from math import ceil
from util import *

class Block():
    def __init__(self, id, data):
        self.id = id
        self.data = data

    def write(self):
        c = len(self.data) + 6
        additional_zeros = ceil(c / 16) * 16 - c
        return struct.pack('<I', len(self.data) + 6 + additional_zeros) + struct.pack('<H', self.id) + self.data + b"\x00" * additional_zeros

def make_string(s):
    if s[-1] == "}":
        s = s[:s.find("{")]
    return struct.pack("<I", len(s)) + s.encode("utf-16le") + b"\x00" * 10

# jump is 10 00 00 00 BE 02 xx xx xx xx ## ## ## ## ## ##
def jump(id):
    return Block(0x2be, struct.pack('<I', id) + b"\x00" * 6)

def parse_params(s):
    a, b = s[s.find("{") + 1:-1].split(";")
    c = bin(int(b, 16))[3:]
    return a, "{},{}".format(len(c) * 85, c)

# there are 21343 sounds in stock voice.afs and we're pushing custom ones to the back
def sound(x):
    return struct.pack("<H", x + 21343)

class x64():
    id = 0x64
    def __init__(self, data, pos, cnt, d, xpos):
        self.read(data)
        self.pos = pos
        self.cnt = cnt
        # meh, dirty hacks
        self.d = d
        self.xpos = xpos

    def read(self, data):
        self.sound = data[0:2]
        self.anim = data[2:4]
        length = struct.unpack("<I", data[4:8])[0] * 2
        self.string = data[8:8 + length].decode("utf-16le")
        self.tail = data[8 + length:]

    def write(self):
        strings = self.string.split("\n")
        first = Block(self.id, self.sound + self.anim + make_string(strings[0]))
        if len(strings) == 1:
            return first, []
        sys.stderr.write("%s from %s [sound id: %d]\n" % (self.string, self.d.blocks[self.xpos], struct.unpack("<H", self.sound)[0]))
        if strings[0][-1] == "}":
            sound_id, dat = parse_params(strings[0])
            if sound_id == "":
                snd = self.sound
            else:
                snd = sound(int(sound_id))
            self.d.blocks.append((snd, dat))
            first = Block(self.id, snd + self.anim + make_string(strings[0]))
        else:
            self.d.blocks.append((self.sound, self.d.blocks[self.xpos]))

        self.d.blocks[self.xpos] = ""

        # local jump to end
        tail = [first]
        first = jump(self.cnt)

        for s in strings[1:]:
            if s[-1] == "}":
                sound_id, dat = parse_params(s)
                magic = sound(int(sound_id)) + self.anim
                self.d.blocks.append((sound(int(sound_id)), dat))
            else:
                magic = b"\xff\xff\xff\xff"
            tail.append(Block(self.id, magic + make_string(s)))
        # jump back
        tail.append(jump(self.pos + 1))
        return first, tail

    def __str__(self):
        return "%s" % self.string

class x68(x64):
    id = 0x68

class x67():
    id = 0x67
    def __init__(self, data):
        self.read(data)

    def read(self, data):
        self.magic = []
        self.strings = []
        self.acnt = []
        self.cnt = struct.unpack("<I", data[0:4])[0]
        self.additions = [[] for x in range(self.cnt)]
        pos = 4
        for x in range(self.cnt):
            self.magic.append(data[pos:pos+4])
            pos += 4
            length = struct.unpack("<I", data[pos:pos+4])[0] * 2
            pos += 4
            self.strings.append(data[pos:pos+length].decode("utf-16le"))
            pos += length

            self.acnt.append(struct.unpack("<I", data[pos:pos+4])[0])
            pos += 4
            for y in range(self.acnt[x]):
                alength = struct.unpack("<I", data[pos:pos+4])[0] * 2
                pos += 4
                self.additions[x].append(data[pos:pos+alength].decode("utf-16le"))
                pos += alength
        self.tail = data[pos:]

    def write(self):
        data = struct.pack("<I", self.cnt)
        for x in range(self.cnt):
            data += self.magic[x]
            data += struct.pack("<I", len(self.strings[x]))
            data += self.strings[x].encode("utf-16le")
            data += struct.pack("<I", self.acnt[x])
            for t in self.additions[x]:
                data += struct.pack("<I", len(t))
                data += t.encode("utf-16le")

        data += self.tail
        return Block(self.id, data), []

    def __str__(self):
        s = ""
        for x in range(self.cnt):
            s += self.strings[x] + " → " + str(self.additions[x]) + "; "
        return s

class x2e01():
    id = 0x12e
    def __init__(self, data):
        self.read(data)

    def read(self, data):
        length = struct.unpack("<I", data[0:4])[0] * 2
        self.string = data[4:4 + length].decode("utf-16le")
        self.tail = data[4 + length:]

    def write(self):
        return Block(self.id, struct.pack("<I", len(self.string)) + self.string.encode("utf-16le") + self.tail), []

    def __str__(self):
        return self.string

class x2303():
    id = 0x323
    def __init__(self, data):
        self.read(data)

    def read(self, data):
        pos = 0
        self.head = struct.unpack("<I", data[pos:pos+4])[0]
        pos += 4
        self.cnt = struct.unpack("<I", data[pos:pos+4])[0]
        pos += 4
        self.strings = []
        self.magic = []
        for x in range(self.cnt + 1):
            length = struct.unpack("<I", data[pos:pos+4])[0] * 2
            pos += 4
            self.strings.append(data[pos:pos+length].decode("utf-16le"))
            pos += length
            if x == 0:
                self.magic.append(b"")
            else:
                self.magic.append(data[pos:pos+0x24])
                pos += 0x24
        self.tail = data[pos:]

    def write(self):
        # works but allows to select same option multiple times and sets visited flag on next entry
        #self.cnt += 1
        #self.strings.append("wobwobwob?")
        #self.magic.append(self.magic[-1])
        #self.magic[-1] = b"\x00" * len(self.magic[-1])

        data = b""
        data += struct.pack("<I", self.head)
        data += struct.pack("<I", self.cnt)
        for x in range(self.cnt + 1):
            data += struct.pack("<I", len(self.strings[x]))
            data += self.strings[x].encode("utf-16le")
            if x != 0:
                data += self.magic[x]
        data += self.tail
        return Block(self.id, data), []

    def __str__(self):
        return str(self.strings)
