#! /bin/sh -

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PYTHON="python"
GPDA="java -cp $DIR/tools Gpda"
GIMCONV="wine $DIR/nonfree/gimconv/GimConv.exe"

fetchStrings=true
buildStrings=true
fetchImages=false
buildImages=false
compile=false
debug=false
fetchMenu=false
buildMenu=false
buildVoice=false
fast=false

if [ ! -f "$DIR/tools/modseekmap"  -o  ! -f "$DIR/tools/Gpda.class" ]; then
    compile=true
fi

while test $# -gt 0
do
    case "$1" in
        --compile) compile=true
            ;;
        --no-fetch-strings) fetchStrings=false
            ;;
        --no-build-strings) buildStrings=false
            ;;
        --debug) debug=true
            ;;
        --fetch-menu) fetchMenu=true
            ;;
        --no-fetch-menu) fetchMenu=false
            ;;
        --build-menu) buildMenu=true
            ;;
        --no-build-menu) buildMenu=false
            ;;
        --build-images) buildImages=true
            ;;
        --no-build-images) buildImages=false
            ;;
        --build-voice) buildVoice=true
            ;;
        --no-build-voice) buildVoice=false
            ;;
        --fast) fast=true
            ;;
        --*) echo "unknown option $1"
            ;;
    esac
    shift
done

if $compile; then
    echo ">> Compiling tools"
    cd $DIR/tools
    g++ modseekmap.cpp -o modseekmap || exit
    javac Gpda.java || exit
fi

echo ">> Cleaning up"
rm "$DIR/out/EBOOT.BIN"
rm "$DIR/out/first.dat"
rm "$DIR/out/first.dat.txt"
rm "$DIR/out/resource.dat"
rm "$DIR/out/resource.dat.txt"
rm "$DIR/out/voice.afs"

if ! $fast; then
    echo ">> Clean working dir"

    rm -rf $DIR/out/first*
    rm -rf $DIR/out/resource*

    cp -r $DIR/source/first* $DIR/out/
    cp -r $DIR/source/resource* $DIR/out/
fi

if $buildVoice; then
    echo ">> Building sounds"
    rm -rf $DIR/data/voice
    rm -rf $DIR/data/voice-mine
    cp -r $DIR/source/voice $DIR/data
    cp -r $DIR/source/voice-mine $DIR/data
    echo ">> .wav -> .ahx"
    cd $DIR/data/voice-mine
    for x in *.wav; do
        wine $DIR/nonfree/ahxencd/ahxencd.exe $x
    done
    cp *.ahx $DIR/data/voice
    echo ">> building .afs"
    cd $DIR/data
    find voice/* | sort > $DIR/data/voice.map
    $DIR/nonfree/afslnk/afslnk voice.map -odir=../out/ voice.afs
    echo ">> patching EBOOT.BIN"
    $PYTHON $DIR/tools/patch-eboot.py $DIR/source/EBOOT.BIN $(ls -1 $DIR/data/voice | wc -l) $DIR/out/EBOOT.BIN
fi

if $fetchStrings; then
    echo ">> Fetching strings"
    rm $DIR/data/strings/*
    cd $DIR/data/strings
    sh $DIR/modules/fetch-strings.sh
fi

if $buildStrings; then
    echo ">> Building strings"
    cd $DIR/data/strings
    echo ">> po2txt"
    for x in *.po; do
        po2txt $x $x.out --fuzzy 2>/dev/null || exit
        echo -n .
    done
    echo ""
fi

echo ">> repack .obj"
# copy old ones
cd $DIR/data/strings
find $DIR/source/resource/script.dat/ -name "*.obj.gz" -exec cp {} . \;
find $DIR/source/resource/script.dat/ -name "*.dat.gz" -exec cp {} . \;
gunzip -f *.gz

if $buildStrings; then
    cd $DIR/data/strings
    for x in *.obj; do
        name=$(echo $x | sed s/.obj$//g)
        $PYTHON $DIR/tools/repack.py $name $DIR/data/obj/$name || exit
        echo -n .
    done
    echo ""
else
    cd $DIR/data/strings
    # just copy em
    for x in *.obj; do
        cp $x $DIR/data/obj/$x
        echo -n .
    done
    for x in *.dat; do
        cp $x $DIR/data/obj/$x
    done
    echo ""
fi

if $debug; then
    echo ">> debug mode"
    cp $DIR/misc/_0000ESS1_debug.obj $DIR/data/obj/_0000ESS1.obj
fi

echo ">> compress .obj"
cd $DIR/data/obj
gzip -n9 -f *.obj
echo ">> replace .obj.gz"
for x in *.obj.gz; do
    name=$(echo $x | sed s/.obj.gz$//g)
    cp $x $DIR/out/resource/script.dat/$name.dat/$name.dat_1/$name.obj.gz
    echo -n .
done
echo ""
gzip -n9 -f *.dat
echo ">> replace .dat"
for x in *.dat.gz; do
    name=$(echo $x | sed s/.dat.gz$//g)
    cp $x $DIR/out/resource/script.dat/$name.dat/$name.dat_1/$name.dat.gz
    echo -n .
done
echo ""

if $buildImages; then
    echo ">> building images"
    cp -r $DIR/images $DIR/data
    # build sg_title
    cd $DIR/data/images/sg_title
    for x in *.png; do
        # this is to convert "Color Type" to "Palette"
        # which makes .gim output much smaller
        pngquant $x -f --ext .png
        $GIMCONV $x -o $x.gim --format_endian little
        mv $x.gim $(echo $x|sed s/.png$//).gim
        echo -n .
    done
    gzip -n9 -f *.gim
    cp *.gim.gz $DIR/out/first/image_sharing.dat/

    cd $DIR/modules/sprites
    sh do.sh
    gzip -n9f out.txt
    pngquant out.png -f --ext .png
    $GIMCONV out.png -o out.gim --format_endian little
    gzip -n9f out.gim
    cp out.gim.gz $DIR/out/resource/image_main.dat/sg_chaname.gim.gz
    cp out.txt.gz $DIR/out/first/text.dat/charaname.txt.gz
fi

cp $DIR/Bhelp_00en.gim.gz $DIR/out/resource/image_block.dat/image_block_title.dat/bhelp_00.gim.gz

echo ">> Packing resource.dat"
cd $DIR/out
$GPDA resource.dat.txt >/dev/null

echo ">> Generating seekmap"
cd $DIR/tools
./modseekmap
cp $DIR/tools/seekmap.new $DIR/out/first
cd $DIR/out/first
gzip -n9 seekmap.new
mv seekmap.new.gz seekmap.dat

if $fetchMenu; then
    echo ">> Fetching menu text"
    curl http://t.minetest.ru/projects/toradora-portable/utf16/en/download/ > $DIR/data/menu.po
    po2txt $DIR/data/menu.po $DIR/data/menu.tmp --fuzzy 2>/dev/null || exit
    sed 'n;d;' $DIR/data/menu.tmp > $DIR/data/menu.txt
fi

if $buildMenu; then
    echo ">> Building menu"
    unix2dos $DIR/data/menu.txt
    iconv -f utf8 -t utf16le $DIR/data/menu.txt > $DIR/data/menu.done
    gzip -n9 -f $DIR/data/menu.done
    cp $DIR/data/menu.done.gz $DIR/out/first/text.dat/utf16.txt.gz
fi

echo ">> Packing first.dat"
cd $DIR/out
$GPDA first.dat.txt >/dev/null

echo ">> Building .ISO"
cd $DIR/out
mv EBOOT.BIN iso/PSP_GAME/SYSDIR/EBOOT.BIN
mv first.dat iso/PSP_GAME/USRDIR/first.dat
mv resource.dat iso/PSP_GAME/USRDIR/resource.dat
mv voice.afs iso/PSP_GAME/USRDIR/voice.afs
mkisofs -sort filelist.txt -iso-level 4 -xa -A "PSP GAME" -V "Toradora" -sysid "PSP GAME" -volset "Toradora" -p "" -publisher "" -o out.iso iso/

echo "== Done!"
