import sys
from distutils.core import setup

if sys.version_info < (3, 9):
    sys.exit('Python 3.9 or higher is required')

setup(
    name='Fall Guys Ping Estimate',
    version='0.5.0',
    description='Provides an overlay which gives an estimate of your current ping to the Fall Guys Servers',
    author='@notatallshaw',
    url='https://github.com/notatallshaw/fall_guys_ping_estimate',
    packages=['fgpe'],
    include_package_data=True,
    install_requires=[
        'psutil'
    ],
)
