.PHONY: install test clean run docker-build docker-run docker-stop

# Development
install:
	python -m pip install --upgrade pip
	pip install -r requirements.txt

test:
	pytest tests/

clean:
	find . -type d -name "__pycache__" -exec rm -r {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.pyd" -delete
	find . -type d -name "*.egg-info" -exec rm -r {} +
	find . -type d -name "*.egg" -exec rm -r {} +
	find . -type d -name ".pytest_cache" -exec rm -r {} +
	find . -type d -name ".coverage" -exec rm -r {} +
	find . -type d -name "htmlcov" -exec rm -r {} +

run:
	python src/main.py

# Docker
docker-build:
	docker-compose build

docker-run:
	docker-compose up -d

docker-stop:
	docker-compose down

docker-logs:
	docker-compose logs -f

# Deployment
deploy:
	@echo "Deploying to production..."
	# Add deployment commands here

# Development environment setup
setup-dev:
	python -m venv .venv
	. .venv/bin/activate && make install
	@echo "Development environment setup complete. Run 'source .venv/bin/activate' to activate the virtual environment." 