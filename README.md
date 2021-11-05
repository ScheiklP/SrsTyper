# SrsTyper
SrsTyper is a learning command line tool to practice typing.
It keeps track of your typos and generates new texts based on a Spaced Repetition System (SRS).

## Getting started
### Requirements
* Any linux distribution that has a `/usr/share/dict/words` file.
* Some python packages, specified in `requirements.txt`

### Starting a session
To start a practice session, just run `python3 main.py` in a terminal.
This will create session information as well as an SRS database in `data`.

## Ideas for future features
* In addition to typos, monitor slow words.
* Create ngrams based on whole words (which words are often typed incorrectly in combination?).
* Design a nice interface that can do more than show the text box and some basic info.
