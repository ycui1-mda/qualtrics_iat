import setuptools

with open("README.md") as file:
    read_me_description = file.read()

setuptools.setup(
    name="qualtrics_iat",
    version="0.1",
    author="Yong Cui",
    author_email="ycui1@mdanderson.org",
    description="A toolset for creating and scoring Qualtrics-based IAT experiments",
    long_description=read_me_description,
    long_description_content_type="text/markdown",
    url="https://github.com/ycui1-mda/qualtrics_iat",
    packages=[''],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.8',
)
