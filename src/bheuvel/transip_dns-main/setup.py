"""Setup.py."""
from setuptools import setup

import codecs
import os.path


def read(rel_path):
    """Open and interpret file."""
    here = os.path.abspath(os.path.dirname(__file__))
    with codecs.open(os.path.join(here, rel_path), "r") as fp:
        return fp.read()


def get_attribute(attribute: str, rel_path: str = "transip_dns/__init__.py") -> str:
    """Get the attribute from the single source of truth."""
    for line in read(rel_path).splitlines():
        if line.startswith(f"__{attribute}__"):
            delimiter = '"' if '"' in line else "'"
            return line.split(delimiter)[1]
    else:
        raise RuntimeError(f"Unable to find {attribute} string.")


setup(
    name="transip-dns",
    description=("TransIP Dns record management script"),
    long_description=open("README.rst").read(),
    long_description_content_type="text/x-rst",
    url="https://github.com/bheuvel/transip_dns",
    version=get_attribute("version"),
    author="Bob",
    author_email="bob.github@heuvel.nu",
    license="MIT",
    keywords="dns transip ddns",
    project_urls={
        "Source": "https://github.com/bheuvel/transip_dns",
        "Tracker": "https://github.com/bheuvel/transip_dns/issues",
    },
    packages=["transip_dns"],
    install_requires=["cryptography", "requests"],
    python_requires=">=3.6",
    entry_points={"console_scripts": ["transip_dns=transip_dns.transip_dns:main"]},
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: English",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Topic :: Internet :: Name Service (DNS)",
        "Topic :: Utilities",
    ],
)
