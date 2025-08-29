from setuptools import setup, find_packages

# Read README.md for long description
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# Read requirements.txt
with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith('#')]

setup(
    name='robstride-sdk',
    version='0.1.0',
    author='RobStride Team',
    author_email='support@robstride.com',
    description='A comprehensive Python SDK for controlling Robstride motors via CAN bus',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/RobStride/robstride-sdk',
    packages=find_packages(),
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Topic :: Scientific/Engineering',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: System :: Hardware :: Hardware Drivers',
    ],
    python_requires='>=3.7',
    install_requires=requirements,
    extras_require={
        'dev': [
            'pytest>=6.0',
            'pytest-cov>=2.0',
            'black>=21.0',
            'flake8>=3.8',
            'mypy>=0.910',
        ],
    },
    entry_points={
        'console_scripts': [
            # Add CLI tools here if needed in the future
        ],
    },
    keywords='robstride motor control can bus robotics actuator',
    project_urls={
        'Documentation': 'https://github.com/RobStride/robstride-sdk',
        'Source': 'https://github.com/RobStride/robstride-sdk',
        'Tracker': 'https://github.com/RobStride/robstride-sdk/issues',
    },
)