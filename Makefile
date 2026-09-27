setup-dirs:
	mkdir -p files/to_convert files/converted

convert-jpg:
	poetry run python image_conversion/main.py --all-jpg
