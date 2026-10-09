.PHONY: install pdfs index app test eval eval-answers demo

install:        ## install dependencies
	pip install -r requirements-dev.txt

pdfs:           ## regenerate the messy demo PDFs
	python scripts/make_demo_pdfs.py

index:          ## build the search index
	python -m src.ingest

app:            ## run the staff web app
	streamlit run app.py

test:           ## unit tests
	python -m pytest -q

eval:           ## retrieval eval (free)
	python -m eval.run_eval

eval-answers:   ## full eval incl. answers (uses API)
	python -m eval.run_eval --answers

demo:           ## ask the demo questions from the CLI
	python ask.py beach-resort "A Gold member wants late checkout on Saturday. How late can they stay?"
	python ask.py mountain-lodge "Can a guest check in early?"
	python ask.py beach-resort "Do we offer babysitting services?"
