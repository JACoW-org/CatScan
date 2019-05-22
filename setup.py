import os
import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="jacowvalidator",
    version="0.0.1",
    author="Australian Synchrotron",
    author_email="ascidev@synchrotron.org.au",
    description="Validate JACoW docx proceedings",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/AustralianSynchrotron/jacow-validator",
    packages=setuptools.find_packages(where="src"),
    package_dir={"": "src"},
    include_package_data=True,
    install_requires=['python-docx', 'python-dotenv', 'flask>=1.0.2', 'flask-uploads', 'titlecase', 'flask-sqlalchemy', 'flask-migrate', 'TexSoup'],
    test_requires=['pytest', 'pytest-cov'],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: BSD 3 Clause",
        "Operating System :: OS Independent",
    ],
    entry_points={
        'console_scripts': [
            'jv=jacowvalidator.cli:cli'
        ],
    },
)
