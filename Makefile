.PHONY: run-prod run-dev

# Production mode: 通常の実行モード
run-prod:
	python app.py

# Development mode: コードの変更を検知して自動リロード
run-dev:
	gradio app.py
