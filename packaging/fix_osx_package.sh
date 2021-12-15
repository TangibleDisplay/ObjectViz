#!/usr/bin/env sh
DIR=dist/ObjectViz.app/Contents/MacOS/

cp $(python -c "import cStringIO; print(cStringIO.__file__)") $DIR
cp -r $(python -c "import importlib, os.path; print(os.path.dirname(importlib.__file__))") $DIR

cat << EOF > $DIR/ObjectViz.sh
#!/usr/bin/env sh
cd "\$(dirname "\${BASH_SOURCE[0]}")"
./ObjectViz
EOF

chmod +x $DIR/ObjectViz.sh
