help:
	@echo "make install    - create venv and install requirements"
	@echo "make test       - run pytest"
	@echo "make run        - run uvicorn locally"
	@echo "make docker     - build and run docker-compose"

install:
	python -m venv venv
	venv\Scripts\activate && pip install -r requirements.txt

test:
	venv\Scripts\activate && pytest -q

run:
	venv\Scripts\activate && uvicorn app:app --reload

docker:
	docker-compose up --build
