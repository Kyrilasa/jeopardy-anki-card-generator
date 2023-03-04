# jeopardy-anki-card-generator

Small program responsible for scraping Jeopardy! questions and generating anki cards from them.


To run the program from command line:
`poetry run python gui.py`

To build it(the executable will be host system specific and reside under the dist/ folder):
`poetry run pyinstaller --onefile -w --icon=app.ico gui.py`