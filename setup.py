"""BorgAPI Package Setup"""
import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="borgapi",
    version="0.6.0-dev.1",
    author="Sean Slater",
    author_email="seanslater@whatno.io",
    description="Wrapper for borgbackup to easily use in code",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/spslater/borgapi",
    license="MIT License",
    packages=setuptools.find_packages(),
    install_requires=["borgbackup==1.1.16", "python-dotenv>=0.17.1"],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Operating System :: OS Independent",
        "License :: OSI Approved :: MIT License",
        "Topic :: Utilities",
    ],
    keywords="borgbackup backup api",
    python_requires=">=3.6",
)
