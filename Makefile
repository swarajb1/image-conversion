setup-dirs:
	mkdir -p files/to_convert files/converted

convert-jpg:
	poetry run python image_conversion/main.py --all-jpg

run:
	poetry run python image_conversion/main.py

rename-only:
	poetry run python image_conversion/main.py --no-convert
