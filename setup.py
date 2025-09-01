from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="robstride-sdk",
    version="1.0.0",
    author="RobStride Team",
    author_email="support@robstride.com",
    description="Python SDK for RobStride motor control via CAN bus",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/robstride/robstride-sdk",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Scientific/Engineering",
        "Topic :: System :: Hardware :: Hardware Drivers",
    ],
    python_requires=">=3.7",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "robstride-cli=robstride_cli:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)
