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
        --no-build-strings) buildsStrings=false
            ;;
        --debug) debug=true
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

echo ">> Clean working dir"

rm -rf $DIR/out/first*
rm -rf $DIR/out/resource*

cp -r $DIR/source/first* $DIR/out/
cp -r $DIR/source/resource* $DIR/out/

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

    echo ">> repack .obj"
    # copy old ones
    find $DIR/source/resource/script.dat/ -name "*.obj.gz" -exec cp {} . \;
    gunzip -f *.gz
    for x in *.obj; do
        $PYTHON $DIR/tools/repack.py $x $DIR/data/obj/$x >/dev/null || exit
        echo -n .
    done
    echo ""

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

echo ">> Packing first.dat"
cd $DIR/out
$GPDA first.dat.txt >/dev/null

echo "== Done!"
