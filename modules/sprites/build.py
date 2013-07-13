#!/usr/bin/env python2
import Image
import os
import sys

prefix = "out"
images = [line.decode("utf-8").rstrip() for line in open("list", "r").readlines()]
width = 512
height = 384
levels = 12

loaded = []
for image in images:
    loaded.append((image, Image.open(os.path.join(prefix, image + ".png"))))

loaded.sort(key=lambda x: -x[1].size[0])

out = Image.new("RGBA", (width, height))

remains = [width for x in xrange(levels)]

fout = open("out.txt", "wb")
for image in loaded:
    inserted = False
    for i in xrange(levels):
        if remains[i] >= image[1].size[0]:
            inserted = True
            x = width - remains[i]
            y = height / levels * i
            out.paste(image[1], (x, y))
            fout.write(("%s,%d,%d,%d,%d,\n" % (image[0], x, y, image[1].size[0], image[1].size[1])).encode("shift-jis"))
            remains[i] -= image[1].size[0]
            break
    if not inserted:
        sys.exit(1)
out.save("out.png")
fout.close()
