#!/usr/bin/env python
"""
A script for downloading VSIX (extensions for VS Code) from the Visual Studio Marketplace, created
because as of June 2023 the Open VSX marketplace (open-vsx.org) does not have all extensions 
available and yet I want to use VS Codium over VS Code.

From https://gist.github.com/wanglf/7acc591890dc0d8ceff1e7ec9af32a55 it appears that the 
path changes sometimes, so I created a script that'd be easier to edit than a bookmarklet.

To summarize how it works:

1. Provide a URL for the extension you want to download, e.g.
    ```
    https://marketplace.visualstudio.com/items?itemName=s3gf4ult.monokai-vibrant
    ```
2. The script requests that page, then identifies the element (currently a JSON-containing
`<script>` tag) that has the necessary information for creating the VSIX URL.
3. It downloads (or prints) that URL.

This is somewhat brittle, so be forewarned. 

## Example Usage

```sh-session
# Given a URL
$ python download-vsix.py https://marketplace.visualstudio.com/items?itemName=s3gf4ult.monokai-vibrant
https://marketplace.visualstudio.com/_apis/public/gallery/publishers/s3gf4ult/vsextensions/monokai-vibrant/0.5.3/vspackage

# ...or just a name
$ python download-vsix.py s3gf4ult.monokai-vibrant
https://marketplace.visualstudio.com/_apis/public/gallery/publishers/s3gf4ult/vsextensions/monokai-vibrant/0.5.3/vspackage

# Given a package spec:
$ python download-vsix.py s3gf4ult.monokai-vibrant@0.5.3
https://marketplace.visualstudio.com/_apis/public/gallery/publishers/s3gf4ult/vsextensions/monokai-vibrant/0.5.3/vspackage

# Download the VSIX package using the script
$ python download-vsix.py s3gf4ult.monokai-vibrant --download --output=/tmp/
Downloading from URL: https://marketplace.visualstudio.com/_apis/public/gallery/publishers/s3gf4ult/vsextensions/monokai-vibrant/0.5.3/vspackage
Saving to: /tmp/s3gf4ult.monokai-vibrant-0.5.3.vsix
```

## Troubleshooting

If it stops working, check that:
```
https://marketplace.visualstudio.com/_apis/public/gallery/publishers/{publisher}/vsextensions/{extension}/{version}/vspackage
```
is still the correct template for VSIX download URLs, and if it is, then the issue is with 
parsing; they've probably changed how they provide the information needed to construct the URL.
"""
__version__ = r"0.0.1"

import argparse
import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import TypeVar, Type
import requests
from bs4 import BeautifulSoup

# Set up logging
log = logging.getLogger(__name__)
logging.basicConfig()

# Typing
T = TypeVar('T')


@dataclass
class Extension:
    """Container for information about a Visual Studio Code extension."""
    name: str
    publisher: str
    version: str = field(default_factory=str)

    def query_version(self, update:bool=True) -> str:
        """Query (and by default, update) the version info from extension name and publisher."""
        if not (res := requests.get(self.marketplace_url)):
            raise RuntimeError(f"Request to {self.marketplace_url} failed ({res.reason})")

        soup = BeautifulSoup(res.content, features="html.parser")
        if (data := soup.find("script", attrs={"class": "jiContent"})) is None:
            raise RuntimeError("Could not find `jiContent` when querying marketplace endpoint.") 

        try:
            info = json.loads(data.text)
            resources = info["Resources"]
            publisher = resources.get("PublisherName")
            extension = resources.get("ExtensionName")
            version = resources.get("Version")
            self.version = version
        except:
            raise 

        return self.version

    @property
    def marketplace_url(self) -> str:
        return f"https://marketplace.visualstudio.com/items?itemName={self.publisher}.{self.name}"

    @property
    def vsix_url(self) -> str:
        if not self.version:
            self.query_version()
        return f"""https://marketplace.visualstudio.com/_apis/public/gallery/publishers/{self.publisher}/vsextensions/{self.name}/{self.version}/vspackage"""

    @property
    def default_filename(self) -> str:
        return f"{self.publisher}.{self.name}-{self.version}.vsix"

    @classmethod
    def from_name(cls: Type[T], extension_spec:str) -> T:
        full_extension, _, version = extension_spec.partition("@")
        publisher, _, name = full_extension.partition(".")
        return cls(name=name, publisher=publisher, version=version)

    @classmethod
    def from_url(cls: Type[T], url: str) -> T:
        if url.startswith(r"https://marketplace.visualstudio.com/items?itemName="):
            ext = url.removeprefix(r"https://marketplace.visualstudio.com/items?itemName=")
            publisher, _, name = ext.partition(".")
            return cls(name=name, publisher=publisher)
        else:
            raise ValueError(f"Failed to understand URL: {url}")


def cli(argv=None):
    parser = argparse.ArgumentParser(argv)
    parser.add_argument("url_or_name", type=str, help="The URL for the extension, e.g. `https://marketplace.visualstudio.com/items?itemName=s3gf4ult.monokai-vibrant`, or just the name (`s3gf4ult.monokai-vibrant` in the example).")
    parser.add_argument("--download", action="store_true", default=False, help="Flag to download the VSIX file, rather than just printing the URL.")
    parser.add_argument("--output", type=Path, default=".", action="store", help="Output path or directory for downloading the VSIX file")
    parser.add_argument('--verbose', '-v', action='count', default=0, help="Increase verbosity of output")
    parser.add_argument('--quiet', action='store_true', default=False, help="Run, printing minimal output. Overrides `--verbose`.")
    parser.add_argument("--debug", action="store_true", default=False, help="Print additional debugging information. Overrides `--verbose` and `--quiet`.")
    parser.add_argument('--version', action='version', version=f"{__version__}")
    args = parser.parse_args()

    log_level = logging.WARNING
    modifier = logging.DEBUG if args.debug else (logging.ERROR if args.quiet else (log_level - 10*args.verbose))
    log.setLevel(modifier)
    

    try:
        ext = Extension.from_url(args.url_or_name)
    except:
        log.info("Couldn't parse as URL, assuming was supplied a name instead...")
        ext = Extension.from_name(args.url_or_name)

    if not ext.version:
        log.info("Version unspecified, getting latest from VS Code Marketplace...")
        log.debug(f"Marketplace URL: {ext.marketplace_url}")
        ext.query_version()

    if not args.download:
        log.debug("No download requested, outputting URL for VSIX file instead...") 
        print(ext.vsix_url)
        return

    # Handle output
    if args.output.is_dir():
        dest = args.output / ext.default_filename
    elif args.output.parent.is_dir():
        dest = args.output 
    else:
        raise ValueError(f"Invalid output path: {args.output}") 

    download_url = ext.vsix_url
    print(f"Downloading from URL: {ext.vsix_url}")
    print(f"Saving to: {dest}")
    res = requests.get(download_url, stream=True)
    with open(dest, "wb") as f:
        for chunk in res.iter_content(chunk_size=None):
            f.write(chunk)
    log.info("Done.")


# https://${publisher}.gallery.vsassets.io/_apis/public/gallery/publisher/${publisher}/extension/${extension name}/${version}/assetbyname/Microsoft.VisualStudio.Services.VSIXPackage
# marketplace_url = r"https://marketplace.visualstudio.com/items?itemName=s3gf4ult.monokai-vibrant"

if __name__ == "__main__":
    cli()


