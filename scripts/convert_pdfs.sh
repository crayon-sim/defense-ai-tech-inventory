#!/usr/bin/env bash
# 국방기술기획서(일반본) PDF 5권을 pdftotext로 변환해 data/source/ 에 넣는다.
# 사용법: scripts/convert_pdfs.sh <PDF가 있는 폴더>
# 필요: poppler-utils (macOS: brew install poppler / Ubuntu: apt install poppler-utils / Windows: https://github.com/oschwartz10612/poppler-windows)
set -euo pipefail
SRC_DIR="${1:-.}"
HERE="$(cd "$(dirname "$0")" && pwd)"
OUT="$HERE/../data/source"
mkdir -p "$OUT"
declare -A MAP=(
  ["22-36"]="2022_22-36_국방기술기획서_일반본"
  ["23-37"]="2023_23-37_국방기술기획서_일반본"
  ["24-38"]="2024_24-38_국방기술기획서_일반본"
  ["25-39"]="2025_25-39_국방기술기획서_일반본"
  ["26-40"]="2026_26-40_국방기술기획서_일반본"
)
for key in "${!MAP[@]}"; do
  pdf=$(ls "$SRC_DIR"/*"$key"*.pdf 2>/dev/null | head -1 || true)
  if [ -z "$pdf" ]; then echo "[skip] $key : PDF 없음"; continue; fi
  echo "[convert] $pdf"
  pdftotext -layout -enc UTF-8 "$pdf" "$OUT/${MAP[$key]}.full.txt"
done
echo "완료. data/source/*.full.txt 를 커밋하거나 업로드해 주세요."
