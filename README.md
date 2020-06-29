Install python:
- build pre-requisites:
$ sudo apt-get build-dep python3.5
$ sudo apt-get install uuid-dev 

- get source
- build python from source:
$ cd Python-3.8.3
$ ./configure && make && make test
$ sudo make altinstall

- setup virtual env:
$ python3.8 -m venv venv3.8
$ pip install numpy scipy ipython
$ pip install nbformat
$ ipython --TerminalInteractiveShell.editing_mode=vi