from os import getenv
from kamidana import (
    as_filter,
    as_globals_generator,
    as_test
)

with open('version.txt') as f:
    version = f.readline().strip()


@as_globals_generator
def generate_globals():
    return {
        "VERSION": version,
        "DEBUG": '-debug' if getenv('WITH_DEBUG') else ''
    }
