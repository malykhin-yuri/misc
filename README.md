Install python 3.8 on Ubuntu 16.04:

- build pre-requisites:
  * sudo apt-get build-dep python3.5
  * sudo apt-get install uuid-dev 

- get source
- build python from source:
  * cd Python-3.8.3
  * ./configure && make && make test
  * sudo make altinstall

- setup virtual env:
  * python3.8 -m venv venv3.8
  * source venv3.8/bin/activate
  * pip install numpy scipy ipython
  * pip install nbformat
  * ipython --TerminalInteractiveShell.editing_mode=vi
