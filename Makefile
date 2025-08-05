# Makefile for BookingAssistant

.PHONY: start stop install test help

help:
	@echo "BookingAssistant Commands:"
	@echo "  make start    - Start all services"
	@echo "  make stop     - Stop all services"
	@echo "  make install  - Install dependencies"
	@echo "  make test     - Run tests"

start:
	python start_all_services.py

stop:
	@echo "Stopping all services..."
	@pkill -f "secure_dashboard_app.py" || true
	@pkill -f "start_slack_endpoint.py" || true
	@pkill -f "run_assistant.py" || true
	@echo "All services stopped."

install:
	pip install -r requirements.txt

test:
	python test_nylas_integration.py

test-email:
	python test_complete_functionality.py

ngrok:
	@echo "Starting ngrok for Slack interactions..."
	ngrok http 8002