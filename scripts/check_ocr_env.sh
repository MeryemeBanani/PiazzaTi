#!/usr/bin/env bash
set -euo pipefail

echo "== OCR environment check =="

echo "Checking pdftoppm (poppler) ..."
if command -v pdftoppm >/dev/null 2>&1; then
  pdftoppm -v || true
else
  echo "pdftoppm NOT FOUND"
fi

echo "Checking tesseract ..."
if command -v tesseract >/dev/null 2>&1; then
  tesseract --version || true
else
  echo "tesseract NOT FOUND"
fi

echo "If either binary is missing, on Debian/Ubuntu install:"
echo "  sudo apt-get update && sudo apt-get install -y poppler-utils tesseract-ocr"
echo "For Italian and English language packs (optional):"
echo "  sudo apt-get install -y tesseract-ocr-ita tesseract-ocr-eng"

exit 0
