import struct
from util import *

class x64():
    def __init__(self, data):
        self.read(data)

    def read(self, data):
        self.magic = data[0:4]
        length = struct.unpack("<I", data[4:8])[0] * 2
        self.string = data[8:8 + length].decode("utf-16le")
        self.tail = data[8 + length:]

    def write(self):
        return self.magic + struct.pack("<I", len(self.string)) + self.string.encode("utf-16le") + self.tail

    def __str__(self):
        return "%s" % self.string

x68 = x64

class x67():
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
        return data

    def __str__(self):
        s = ""
        for x in range(self.cnt):
            s += self.strings[x] + " → " + str(self.additions[x]) + "; "
        return s

class x2e01():
    def __init__(self, data):
        self.read(data)

    def read(self, data):
        length = struct.unpack("<I", data[0:4])[0] * 2
        self.string = data[4:4 + length].decode("utf-16le")
        self.tail = data[4 + length:]

    def write(self):
        return struct.pack("<I", len(self.string)) + self.string.encode("utf-16le") + self.tail

    def __str__(self):
        return self.string

class x2303():
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
        data = b""
        data += struct.pack("<I", self.head)
        data += struct.pack("<I", self.cnt)
        for x in range(self.cnt + 1):
            data += struct.pack("<I", len(self.strings[x]))
            data += self.strings[x].encode("utf-16le")
            if x != 0:
                data += self.magic[x]
        data += self.tail
        return data

    def __str__(self):
        return str(self.strings)
