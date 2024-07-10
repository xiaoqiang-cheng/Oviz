#!/bin/bash
# requirement
# pip install build
# pip install twine

python -m build
twine upload dist/* --verbose