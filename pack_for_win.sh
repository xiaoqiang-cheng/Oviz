set -e
pyinstaller main.spec
mkdir -p dist/main/_internal/Oviz/
cp -r Oviz/Config dist/main/_internal/Oviz/