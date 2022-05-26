import unrealsdk
import importlib
import os
import re
import shlex
#from typing import List, Optional, Tuple

# Import all files in this director - we want the side effects (which register everything)
_dir = os.path.dirname(__file__)
for file in os.listdir(_dir):
    if not os.path.isfile(os.path.join(_dir, file)):
        continue
    if file == "__init__.py":
        continue
    name, suffix = os.path.splitext(file)
    if suffix != ".py":
        continue

    importlib.import_module("." + name, __name__)
del _dir, file
