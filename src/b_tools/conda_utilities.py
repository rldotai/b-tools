"""
Some attempts at making `conda`/`mamba` more convenient to work with.
"""
import argparse
import sys
from pathlib import Path

from . import common
__version__ = common.get_version()


def export_env_cli(argv=None):
    print("export_env_cli")
    parser = argparse.ArgumentParser()

    # Required positional argument
    parser.add_argument(
        "name",
        nargs="?",
        help="Name of environment to export. Defaults to current active environment.",
    )
    parser.add_argument(
        "--prefix",
        type=Path,
        default=None,
        help="Full path to environment, that is, the `conda` prefix.",
    )

    # Optional parameters and flags
    parser.add_argument(
        "-f",
        "--file",
        action="store",
        dest="filename",
        default=None,
        help="Write output to file instead of printing.",
    )
    # TODO: mutually exclusive with `--file`
    parser.add_argument(
        "--json",
        action="store_true",
        default=False,
        help="Return output in JSON format.",
    )
    parser.add_argument(
        "--dry-run",
        dest="dry_run",
        action="store_true",
        default=False,
        help="Run script without changing any files.",
    )

    # Optional verbosity counter (eg. -v, -vv, -vvv, etc.)
    parser.add_argument(
        "-v", "--verbose", action="count", default=0, help="Verbosity (-v, -vv, etc)"
    )
    # TODO: actually adjust logging verbosity based on this

    # Specify output of "--version"
    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s (version {version})".format(version=__version__),
    )

    args = parser.parse_args()
    print(args)



if __name__ == "__main__":
    print(f"{__name__=}")
    export_env_cli()