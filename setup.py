from setuptools import setup, find_packages

setup(
    name='echomatrix',
    version='0.1.0',
    packages=find_packages(),
    install_requires=[
        'requests',
        'soundfile',
        'openai',
        'pydub',
        'pyyaml',
        'pyst'  # For Asterisk AGI
    ],
    entry_points={
        'console_scripts': [
            'echomatrix-agi=echomatrix.agi_handler:main',
            'echomatrix=echomatrix.cli:main',  # Main CLI entry point
        ],
    },
)