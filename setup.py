from setuptools import setup

NAME = "Gulf"
VERSION = "0.1"

setup(
    name=NAME,
    version=VERSION,
    entry_points={
        "console_scripts": [
            "gulf = gulf.main:deploy"
        ]
    }
)
