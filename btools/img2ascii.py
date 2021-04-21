#!/usr/bin/env python3
"""
Converts an image to ASCII art
"""
import argparse
import io
import logging
import shlex
import shutil
import subprocess
import sys
from pathlib import Path
from common import is_executable


logger = logging.getLogger(__name__)


def main(argv=None):
    """Parse arguments and run the script."""

    # Create parser
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "input",
        type=argparse.FileType('r'),
        help="Path to input image file",
    )
    parser.add_argument(
        "output",
        nargs='?',
        type=argparse.FileType("wb"),
        default=sys.stdout,
        help=("Path to output file. If unspecified, uses stdout."),
    )
    parser.add_argument(
        "--backend",
        choices={"imagemagick", "jp2a"},
        type=str.lower,
        default="imagemagick",
        help="Backend to use for creating the ASCII art.",
    )
    parser.add_argument(
        "--geometry",
        default="80x24",
        help="Width and height (in terms of characters) for the output.",
    )
    parser.add_argument(
        "--negate",
        action="store_true",
        default=False,
        help="Whether to take the negative of the image to be converted.",
    )
    parser.add_argument(
        "--ncolors",
        type=int,
        default=2,
        help="The number of colors to use.",
    )



    # Set logging verbosity
    verbosity = parser.add_mutually_exclusive_group()
    verbosity.add_argument(
        "--verbose",
        "-v",
        action="store_const",
        const=logging.DEBUG,
        default=logging.INFO,
        help="Turn on debug logging.",
    )
    verbosity.add_argument(
        "-q",
        "--quiet",
        dest="verbose",
        action="store_const",
        const=logging.ERROR,
        help="Turn off debug logging except for reporting errors.",
    )
    args = parser.parse_args(argv)

    # Set logging levels
    logger.setLevel(args.verbose)

    # Log input arguments
    logger.debug(f"args: {vars(args)}")

    # Handle input from stdin
    if args.input.fileno() == 0:
        raise ValueError("I haven't implemented handling piped input yet :(")
    elif isinstance(args.input, io.IOBase):
        input_path = Path(args.input.name)
        if not input_path.is_file():
            raise ValueError("Non-file input path: {input_path}")

    # Choose between backends
    if args.backend == "imagemagick":
        __func = img2ascii_imagemagick
        kwargs = {
            "geometry": args.geometry,
            "negate": args.negate,
            "ncolors": args.ncolors,
        }
    else:
        raise ValueError(f"Unknown backend provided: {args.backend}")


    # Create output
    result = __func(input_path, **kwargs)

    # Save / produce the result
    with args.output as f:
        f.write(result)


def img2ascii_imagemagick(input_path, geometry="160x160", negate=True, ncolors=2):
    """Convert an image to ASCII representation using ImageMagick.

    See: https://imagemagick.org/script/command-line-processing.php
    """
    # Look for the ImageMagick binary
    if (exec_path := shutil.which('magick')) is not None:
        logger.debug(f"Using `{exec_path}` for ImageMagick")
        cmd = [exec_path, "convert"]
    elif (exec_path := shutil.which('convert')) is not None:
        logger.debug(f"Using `{exec_path}` for ImageMagick")
        cmd = [exec_path]
    else:
        logger.error("No binary for ImageMagick found")

    # Build the command
    args = [
        f"{input_path}",
        f"-geometry {geometry}",
        f"-colors {ncolors}",
        "-negate" if negate else "",
        f"xpm:",
    ]

    # Run the command -- I can't find a way to do this w/o `shell=True`
    result = subprocess.run(" ".join([*cmd, *args]), capture_output=True, timeout=10, shell=True)
    output = result.stdout.decode('utf-8')

    # TODO: Maybe process header since it gives some info
    ret = []
    in_body = False

    for line in output.split("\n"):
        line = line.strip()
        if in_body:
            if line.startswith(r'"'):
                ret.append(line.lstrip(r'"').rstrip(r'",'))
        else:
            if "pixels" in line.strip():
                in_body = True
            else:
                # Here's where header processing would happen
                pass
    ret.append("\n")
    return "\n".join(ret)


def img2ascii_jp2a():
    """Convert an image to an ASCII art representation using `jp2a`.

    Example:
        magick convert examples/lineart_1.webp -negate jpg:- | jp2a --width=80 -

    See also:
        - https://csl.name/jp2a/
    """

if __name__ == "__main__":
    main()
