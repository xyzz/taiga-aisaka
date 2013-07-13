echo ">> Fetching images"
python3 fetch.py
cd source
echo ">> Processing images"
for x in *.png; do
	echo -n .
	convert $x -bordercolor none -border 1 -trim ../out/$x 2>/dev/null
done
echo ""
cd ..
echo ">> Building sprite map"
python2 build.py >/dev/null
