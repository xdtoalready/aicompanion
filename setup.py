from setuptools import setup, find_packages

setup(
    name="aicompanion",
    version="0.1.0",
    packages=find_packages(include=["app", "app.*"]),
)
