from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="videoenhance",
    version="0.1.0",
    author="VideoEnhance Contributors",
    description="Automated video enhancement pipeline for SD interlaced content",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: End Users/Desktop",
        "Topic :: Multimedia :: Video :: Conversion",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=[
        "vapoursynth>=60",
        "ffmpeg-python>=0.2.0",
        "numpy>=1.24.0",
        "Pillow>=10.0.0",
        "av>=10.0.0",
        "click>=8.1.0",
        "rich>=13.0.0",
        "tqdm>=4.65.0",
        "pyyaml>=6.0",
        "toml>=0.10.2",
        "watchdog>=3.0.0",
        "psutil>=5.9.0",
    ],
    extras_require={
        "gui": ["PyQt6>=6.5.0"],
    },
    entry_points={
        "console_scripts": [
            "videoenhance=videoenhance.cli:main",
        ],
    },
)
