#! /bin/sh -

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PYTHON="python"
GPDA="java -cp $DIR/tools Gpda"

fetchStrings=true
buildStrings=true
fetchImages=false
buildImages=false
compile=false
debug=false
fetchMenu=false
buildMenu=false
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

if ! $fast; then
    echo ">> Clean working dir"

    rm -rf $DIR/out/first*
    rm -rf $DIR/out/resource*

    cp -r $DIR/source/first* $DIR/out/
    cp -r $DIR/source/resource* $DIR/out/
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
        $PYTHON $DIR/tools/repack.py $name $DIR/data/obj/$name >/dev/null || exit
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
        wine $DIR/nonfree/gimconv/GimConv.exe $x -o $x.gim --format_endian little
        mv $x.gim $(echo $x|sed s/.png$//).gim
        echo -n .
    done
    gzip -n9 -f *.gim
    cp *.gim.gz $DIR/out/first/image_sharing.dat/
fi

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

echo "== Done!"
