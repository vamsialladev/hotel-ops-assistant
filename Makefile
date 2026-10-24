.PHONY: install pdfs index app test lint audit eval eval-answers eval-visitors demo screenshots secrets video

install:        ## install dependencies
	pip install -r requirements-dev.txt

pdfs:           ## regenerate the messy demo PDFs
	python scripts/make_demo_pdfs.py

index:          ## build the search index
	python -m src.ingest

secrets:        ## build .streamlit/secrets.toml from .env (prints key names only)
	python scripts/make_secrets.py

app:            ## run the staff web app
	streamlit run app.py

test:           ## unit tests with coverage
	python -m pytest -q --cov=src --cov=eval

lint:           ## lint and format check
	ruff check . && ruff format --check .

audit:          ## known vulnerabilities in dependencies
	pip-audit -r requirements.txt

eval:           ## retrieval eval (free)
	python -m eval.run_eval

eval-answers:   ## full eval incl. answers, 3 runs, with cost (uses the API)
	python -m eval.run_eval --answers --runs 3 --price-in 0.10 --price-out 0.50

eval-visitors:  ## visitor first-question eval: routing and retrieval (free)
	python -m eval.run_visitor_eval --bm25-only

video:          ## record the captioned demo video (no voice) from the live app (6 real questions)
	python scripts/record_demo.py

screenshots:    ## README screenshots and GIF (app must be running)
	python scripts/capture_screenshots.py

demo:           ## ask the demo questions from the CLI
	python ask.py beach-resort "A Gold member wants late checkout on Saturday. How late can they stay?"
	python ask.py mountain-lodge "Can a guest check in early?"
	python ask.py beach-resort "Do we offer babysitting services?"
