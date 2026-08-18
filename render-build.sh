#!/usr/bin/env bash

apt-get update
apt-get install -y tesseract-ocr tesseract-ocr-eng tesseract-ocr-rus

pip install -r requirements.txt
