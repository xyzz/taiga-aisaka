import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.RandomAccessFile;
import java.util.Arrays;

public class Gpda {
    static final String CHARSET = "SJIS";
    static final int DAT_BLOCK_SIZE = 2048;
    static final byte[] GPDA_SIG = new byte[] {71,80,68,65};
    static final byte[] GZIP_SIG = new byte[] {31,(byte)139,8,0};

    static final int FILE_BUFFER_SIZE = 5120000;
    static boolean gzip = false;

    public Gpda() {
    }

    int findDupName(int cur, String name, String[] names) {
        int count = 0;
        for (int i=0; i<names.length;i++) {
            if (names[i].equals(name)) {
                if (cur < i) {
                    return count;
                }
                count++;
            }
        }
        if (count>1) {
            return count;
        }
        return -1;
    }

    void extractGpda(RandomAccessFile in, long offset, int size, String output, FileOutputStream datlist, String infostring, byte[] indexname) {
        try {
            byte[] buffer = new byte[4];
            in.seek(offset);
            in.read(buffer, 0, 4);

            if (Arrays.equals(GPDA_SIG,buffer)) {
                int filecount,namesize,sameNum;
                int[] filesizes, nameoffsets;
                long filesize;
                long[] fileoffsets;
                String[] filelist;
                byte[][] indexnames;
                String filename;

                filesize = Long.reverseBytes(in.readLong());
                filecount = Integer.reverseBytes(in.readInt());
                fileoffsets = new long[filecount];
                filesizes = new int[filecount];
                nameoffsets = new int[filecount];
                filelist = new String[filecount];
                indexnames = new byte[filecount][];

                for (int i=0; i<filecount; i++) {
                    fileoffsets[i] = Long.reverseBytes(in.readLong());
                    filesizes[i] = Integer.reverseBytes(in.readInt());
                    nameoffsets[i] = Integer.reverseBytes(in.readInt());
                }
                for (int i=0; i<filecount; i++) {
                    in.seek((long)nameoffsets[i]+offset);
                    namesize = Integer.reverseBytes(in.readInt());
                    indexnames[i] = new byte[namesize];
                    in.read(indexnames[i], 0, namesize);
                    filelist[i] = new String(indexnames[i], CHARSET);
                }
                System.out.println("Extracting: "+output);
                new File(output).mkdir();

                datlist.write(("d"+infostring).getBytes());
                datlist.write(indexname);
                datlist.write("\r\n".getBytes());

                for (int i=0; i<filecount; i++) {
                    sameNum = findDupName(i, filelist[i], filelist);
                    filename = output+"/"+filelist[i].trim();
                    if (sameNum > 0) {
                        extractGpda(in, fileoffsets[i]+offset, filesizes[i], filename+"_"+sameNum, datlist, sameNum+","+output+"/", indexnames[i]);
                    } else {
                        extractGpda(in, fileoffsets[i]+offset, filesizes[i], filename, datlist, ","+output+"/", indexnames[i]);
                    }
                }
            } else if (offset==0) {
                System.out.println("not a GPDA file");
            } else if (gzip && Arrays.equals(GZIP_SIG,buffer)) {
                int read;
                String filename = output;
                FileOutputStream out;
                if (output.endsWith(".gz")) {
                    datlist.write(("g"+infostring).getBytes());
                    datlist.write(indexname);
                    datlist.write("\r\n".getBytes());
                } else {
                    filename = output+".gz";
                    datlist.write(("e"+infostring).getBytes());
                    datlist.write(indexname);
                    datlist.write("\r\n".getBytes());
                }
                in.seek(offset);
                buffer = new byte[FILE_BUFFER_SIZE];
                out = new FileOutputStream(filename);
                for (int r=0;r<size;r+=read) {
                    read = in.read(buffer, 0, Math.min(FILE_BUFFER_SIZE,size-r));
                    if (read <= 0) {
                        return;
                    }
                    out.write(buffer, 0, read);
                }
                out.close();
                System.out.println("Extracting: "+filename);
                Runtime.getRuntime().exec(new String[] {"gzip", "-df", filename});
                //does not wait for and check if extracted file is a gpda file
            } else {
                int read;
                FileOutputStream out;
                in.seek(offset);
                buffer = new byte[FILE_BUFFER_SIZE];
                System.out.println("Writing: "+output);

                datlist.write(("f"+infostring).getBytes());
                datlist.write(indexname);
                datlist.write("\r\n".getBytes());
                out = new FileOutputStream(output);
                for (int r=0;r<size;r+=read) {
                    read = in.read(buffer, 0, Math.min(FILE_BUFFER_SIZE,size-r));
                    if (read <= 0) {
                        return;
                    }
                    out.write(buffer, 0, read);
                }
                out.close();
            }
        } catch (Exception e) {
            System.out.println(e.getMessage());
        }
    }

    void writeSig(RandomAccessFile out, long offset, int filecount) throws Exception {
        out.seek(offset);
        out.write(GPDA_SIG, 0, 4);
        if (filecount == 0) {
            out.writeInt(Integer.reverseBytes(DAT_BLOCK_SIZE));
            out.seek(offset+DAT_BLOCK_SIZE-1);
            out.writeByte(0);
            return;
        }
        out.seek(offset+12);
        out.writeInt(Integer.reverseBytes(filecount));
    }

    int writeIndexNames(RandomAccessFile out, long offset, byte[][] list) throws Exception {
        int filecount = list.length;
        int size_index = filecount*16+16;
        int size_names = 0;
        for (int i=0; i<filecount; i++) {
            out.seek(offset+28+i*16);
            out.writeInt(Integer.reverseBytes(size_index+size_names));
            size_names += list[i].length+4;
        }
        out.seek(offset+size_index);
        for (int i=0; i<filecount; i++) {
            out.writeInt(Integer.reverseBytes(list[i].length));
            out.write(list[i], 0, list[i].length);
        }
        return size_index+size_names;
    }

    void writeIndexFiles(RandomAccessFile out, long offset, long fileoffset, int filesize) throws Exception {
        out.seek(offset);
        out.writeLong(Long.reverseBytes(fileoffset));
        out.writeInt(Integer.reverseBytes(filesize));
    }

    void writeDatSize(RandomAccessFile out, long offset, long size) throws Exception {
        out.seek(offset+4);
        out.writeLong(Long.reverseBytes(size));
    }

    int getBlockSize(int size) {
        if (size > 0) {
            return (int)(Math.ceil((double)size/DAT_BLOCK_SIZE)*DAT_BLOCK_SIZE);
        } else {
            return DAT_BLOCK_SIZE;
        }
    }

    long writeFile(File input, RandomAccessFile out, long offset) throws Exception {
        long current_filesize = input.length();
        byte[] buffer = new byte[FILE_BUFFER_SIZE];
        FileInputStream in = new FileInputStream(input);
        int bytes_read;
        out.seek(offset);
        for (int total_bytes_read=0;total_bytes_read<current_filesize;total_bytes_read += bytes_read) {
            bytes_read = in.read(buffer, 0, FILE_BUFFER_SIZE);
            if (bytes_read > 0) {
                out.write(buffer, 0, bytes_read);
            } else {
                return -1;
            }
        }
        in.close();
        return current_filesize;
    }

    private class Node {
        int depth;
        String id,path;
        Node next,parent,child;
        byte[] indexname;

        Node(Node parent, String id, byte[] indexname, String path, int depth) {
            this.parent = parent;
            this.id=id;
            this.indexname = indexname;
            this.path = path;
            this.depth = depth;
            this.child = this.next = null;
        }

    }

    int getDepth(String path) {
        int depth = 0;
        for (int i=0;i<path.length();i++) {
            if (path.charAt(i)=='/') {
                depth++;
            }
        }
        return depth;
    }

    int _fcurrent=0;
    int _fcurrentsize=0;
    byte[] _fbuffer = new byte[4096000];

    byte[] readLine(FileInputStream datlist) throws Exception {
        int start = _fcurrent;
        if (_fcurrentsize==0) {
            _fcurrentsize = datlist.read(_fbuffer, 0, _fbuffer.length);
        }
        int nl = -2;
        for (;_fcurrent<_fcurrentsize;_fcurrent++) {
            if (_fbuffer[_fcurrent] == (byte)13) {
                nl = _fcurrent;
            } else if (nl == _fcurrent-1 && _fbuffer[_fcurrent] == (byte)10) {
                _fcurrent++;
                byte[] ret = new byte[nl-start];
                for (int j=0;j<nl-start;j++) {
                    ret[j] = _fbuffer[j+start];
                }
                return ret;
            }
        }
        if (_fcurrentsize > 0) {
            int copy = _fbuffer.length-start;
            System.arraycopy(_fbuffer, start, _fbuffer, 0, copy);
            _fcurrent = 0;
            _fcurrentsize = datlist.read(_fbuffer, copy, _fbuffer.length-copy);
            if (_fcurrentsize <= 0) {
                return null;
            }
            _fcurrentsize+= copy;
            return readLine(datlist);
        }
        return null;
    }

    void readDatlist(FileInputStream datlist, Node p) throws Exception {
        int depth,cs,ls;
        String path,id;
        Node c;
        byte[] indexname;

        for (byte[] byteline=readLine(datlist);byteline!=null;byteline=readLine(datlist)) {
            String line = new String(byteline, CHARSET);
			//System.out.println(line);
            cs = line.indexOf(',');
            ls = line.lastIndexOf('/');
            id = line.substring(0, cs);
            path = line.substring(cs+1, ls);
            depth = getDepth(line);
            indexname = new byte[byteline.length-ls-1];
            System.arraycopy(byteline, ls+1, indexname, 0, byteline.length-ls-1);
            if (depth == p.depth+1) {
                p=p.child = new Node(p, id, indexname,path,depth);
            } else if (depth == p.depth) {
                p=p.next = new Node(p, id, indexname,path,depth);
            } else {
                for (c = p; c!=null && depth < c.depth;c=c.parent) {}
                p=c.next=new Node(c, id, indexname,path,depth);
            }
        }
    }

    long writeGpda(RandomAccessFile out, long offset, FileInputStream datlist) {
        try {
            byte[] l = readLine(datlist);
			String line = new String(l);
            System.out.println(line);
			if (line.startsWith("d,")) {
                String name = line.substring(2);
                Node start = new Node(null, "d", name.getBytes(),"",0);
                readDatlist(datlist, start);
                return _writeGpdaWithTxt(out, offset, start.child);
            } else {
				System.out.println("failed");
                return -1;
            }
        } catch (Exception e) {
            System.out.println(e.getMessage());
            return -1;
        }
    }

    long _writeGpdaWithTxt(RandomAccessFile out, long offset, Node filelist) {
        long written_bytes = 0;
        try {
			System.out.println("_writeGpdaWithTxt");
            int filecount = 0;
            for (Node c=filelist;c != null; c=c.next) {
                filecount++;
            }
			System.out.println(filecount);
            byte[][] list = new byte[filecount][];
            int t=0;
            for (Node c=filelist;c != null; c=c.next) {
                list[t] = c.indexname;
                t++;
            }
            writeSig(out, offset, filecount);
            if (filecount==0) {
                return DAT_BLOCK_SIZE;
            }

            written_bytes += getBlockSize(writeIndexNames(out, offset, list));

            String current_file;
            long current_filesize;
            int i=0;
            for (Node c=filelist;c != null; c=c.next) {
                current_file = c.path+"/"+new String(c.indexname, CHARSET).trim();
                System.out.println("Adding: "+current_file);
                if (c.id.charAt(0) == 'd') {
                    current_filesize = _writeGpdaWithTxt(out,offset+written_bytes,c.child);
                    if (current_filesize < 0) {
                        return current_filesize;
                    }
                } else {
                    if (c.id.length()>1) {
                        current_file = current_file+"_"+c.id.substring(1);
                    }
                    if (gzip && c.id.charAt(0)== 'g') {
                        Process p = Runtime.getRuntime().exec(new String[] {"gzip", "-fkn9", current_file.substring(0, current_file.lastIndexOf('.'))});
                        p.waitFor();
                        File tmp = new File(current_file);
                        current_filesize = writeFile(tmp, out, offset+written_bytes);
                        tmp.delete();
                    } else if (gzip && c.id.charAt(0) == 'e') {
                        Process p = Runtime.getRuntime().exec(new String[] {"gzip", "-fkn9", current_file});
                        p.waitFor();
                        File tmp = new File(current_file+".gz");
                        current_filesize = writeFile(tmp, out, offset+written_bytes);
                        tmp.delete();
                    } else {
                        current_filesize = writeFile(new File(current_file), out, offset+written_bytes);
                    }
                }
                if (current_filesize < 0) {
                    return current_filesize;
                }
                writeIndexFiles(out, offset+16+i*16, written_bytes, (int)current_filesize);
                current_filesize = getBlockSize((int)current_filesize);
                written_bytes += current_filesize;
                i++;
            }
            writeDatSize(out, offset, written_bytes);
            return written_bytes;
        } catch (Exception e) {
            System.out.println(e.getMessage());
            return -1;
        }
    }

    void start(String file) {
        try {
            File f = new File(file);
            if (f.isDirectory()) {
            } else if (file.endsWith(".dat.txt")) {
                FileInputStream datlist = new FileInputStream(file);
                String filename = file.substring(0, file.length()-8);
                f = new File(filename+".dat");
                if (f.exists()) {
                    f.delete();
                }
                RandomAccessFile out = new RandomAccessFile(f, "rw");
                long ret = writeGpda(out, 0, datlist);
                if (ret > 0 && out.length() != ret) {
                    out.seek(ret-1);
                    out.writeByte(0);
                }
                out.close();
            } else if (file.endsWith(".dat")) {
                RandomAccessFile in = new RandomAccessFile(f, "r");
                FileOutputStream datlist = new FileOutputStream(file+".txt");
                String name = file.substring(0, file.length()-4);
                extractGpda(in, 0, 0, name, datlist, ",", name.getBytes());
                in.close();
                datlist.close();
            }
            System.out.println("end");
        } catch (Exception e) {
            System.out.println(e.getMessage());
        }
    }

    public static void main(String[] args) {
        if (args.length == 1) {
            new Gpda().start(args[0]);
        } else if (args.length == 2) {
            if (args[1].equals("gzip")) {  //gzip.exe is needed, recompressing can change some files,
                gzip = true;               //without this option and without changing files
            }                              //should produce exactly the same .dat as the original
            new Gpda().start(args[0]);
        } else {
            System.out.println("To unpack: java Gpda <filename>.dat [gzip]");
            System.out.println("To pack: java Gpda <filename>.dat.txt [gzip]");
        }
    }
}
