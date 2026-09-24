import pathlib
import sys

# type_gen lives in scripts/ (not tests/) because it generates
# production code, not test fixtures.
sys.path.insert(0,
                str(pathlib.Path(__file__).parent.parent.parent / "scripts"))
