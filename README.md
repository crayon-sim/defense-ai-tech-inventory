# 국방기술과제 인벤토리 (Defense Technology Project Inventory)

국방기술진흥연구소가 매년 발간하는 「국방기술기획서(일반본)」 ’22-’36 · ’23-’37 · ’24-’38 · ’25-’39 · ’26-’40 다섯 권에 수록된
**국방기술과제**를 한 곳에 모아, 미 연방정부 관리예산처(OMB)의
[2025 Federal Agency AI Use Case Inventory 보고 지침](https://github.com/ombegov/2025-Federal-Agency-AI-Use-Case-Inventory/blob/main/Reporting%20Instructions/Reporting%20Instructions.md)과
[통합 인벤토리 저장소](https://github.com/ombegov/2025-Federal-Agency-AI-Use-Case-Inventory) 형식을 참고해 정리한 정적 사이트와 데이터셋입니다.

- 사이트: GitHub Pages (저장소 설정에서 Pages → Source를 *GitHub Actions*로 지정하면 `.github/workflows/pages.yml`이 배포)
- 로컬 실행: 저장소 루트에서 `python3 -m http.server 8000` 후 <http://localhost:8000> 접속 (JSON을 fetch하므로 `file://`로는 열리지 않음)

## 구성

| 화면 | 내용 |
|------|------|
| 대시보드 | 과제 수·상태·예산 요약, 분야별 / 사업구분별 / 기획서 연도별 분포, 인공지능 분야 국방전략기술별 과제, ’26-’40 기술개발소요(Lv.4) 분야별 집계 |
| 과제 인벤토리 | 1행 1과제 표. 검색·분야·국방전략기술·사업구분·상태·수록 연도·무기체계 분야 필터, 정렬, 과제 상세(개요·연구항목·연도별 수록 내역·변경 사항), CSV/JSON 다운로드 |
| 국방전략기술 체계 | 10대 분야 → 30개 국방전략기술(Lv.1) → 세부기술(Lv.2) → 구성기술(Lv.3, ’26-’40 기술트리)과 연계 과제, ’23-’37 국방기술 목록, ’22-’36 체계(8대 분야 99개 국방전략기술·핵심기술) |
| 연도별 변화 | 같은 과제의 사업기간·사업구분·분류·예산·과제명 변경, 최신 과제 목록 미수록 과제 |
| 데이터 안내 | 병합 원칙, 기획서별 반영 범위, OMB 항목 대응표 |

## 데이터

| 파일 | 설명 |
|------|------|
| `data/inventory.json` | 과제별 전체 필드(연도별 이력 `editions`, 과제카드 `card`, 변경 사항 `changes` 포함) |
| `data/inventory.csv` | 평면 표(UTF-8 BOM), 1행 1과제 |
| `data/taxonomy.json` | 국방전략기술 체계와 연계 과제, ’23-’37 국방기술, ’22-’36 체계, ’26-’40 Lv.4 집계 |
| `data/stats.json` | 대시보드용 집계 |
| `data/DATA_DICTIONARY.md` | 필드 정의와 OMB 항목 대응 |
| `data/source/full/` | ’23-’37~’26-’40 기획서 전문 텍스트(`tools/pdf2text.html`로 변환) |
| `data/source/` | ’22-’36 기획서 등 Google Drive 텍스트 변환본(앞부분만) |
| `data/intermediate/` | 기획서별 파싱 결과 |

현재 수록 규모(2026-10 기준)

| 항목 | 값 |
|------|----|
| 고유 과제 | 1,254건 |
| ’26-’40 과제 목록(최신 전체 목록) | 459건 |
| 기획서별 수록 과제 | ’22-’36 588 · ’23-’37 859 · ’24-’38 775 · ’25-’39 653 · ’26-’40 459 |
| 과제카드(개요·연구항목)가 있는 과제 | 1,055건 |
| 국방전략기술 연계 과제 / 인공지능 분야 | 632건 / 43건 |

### 병합 원칙 — 최신자료 우선

1. 같은 과제가 여러 기획서에 실린 경우, 과제명·사업구분·기간·주관형태·예산·개요는 **가장 최신 기획서**의 값을 쓴다.
2. 국방전략기술 분야는 ’26-’40 과제 목록 기준, 국방전략기술·세부기술은 ’25-’39 제2장(없으면 ’24-’38, ’23-’37) 기준이다. 분야가 서로 다르면 `strategic_tech_note`에 표시한다.
3. 과제번호는 발간 연도마다 다시 매겨지므로 연도별 번호는 `editions.{연도}.project_no`에 보관하고, 사이트 식별자 `KDTI-####`를 별도로 부여한다.
4. 과제 동일성은 과제명을 정규화(공백·기호 제거)해 판정하고, 명칭이 크게 바뀐 과제는 `scripts/build_inventory.py`의 `RENAMED_PROJECTS` 표로 수동 연결한다.
5. 상태(착수 예정 · 진행 중 · 종료)는 2026년을 기준으로 사업기간에서 산출하고, 기획서에 명시된 진행과제/예정과제 표기는 이력으로 보관한다.
6. 최신 과제 목록(’26-’40)에 없는 과거 과제는 삭제하지 않고 "최신 과제 목록 미수록"으로 표시한다.

### 기획서별 반영 범위

| 기획서 | 반영 범위 |
|--------|-----------|
| ’22-’36 | 제2장 8대 분야 99개 국방전략기술 · 핵심기술 목록과 반영과제(590건). 제3·4장은 제공된 PDF(resized본)의 글꼴 매핑 손상으로 텍스트 추출 불가 |
| ’23-’37 | 제2장 10대 분야 30개 국방전략기술별 국방기술·진행/예정과제 전체, 제3장 과제 목록 전체(기초연구~민·군기술협력 853건), 부록 과제카드 846건 |
| ’24-’38 | 제2장 전체, 제3장 과제 목록 전체(778건 중 772건), 부록 과제카드 775건 |
| ’25-’39 | 제2장 전체(30개 국방전략기술·92개 세부기술·연계 과제 377건), 제3장 과제 목록 644건, 부록 과제카드 644건 |
| ’26-’40 | 제2장 10대 분야 기술트리(Lv.1 30 · Lv.2 ~100 · Lv.3 ~300)와 기술개발소요 집계, 제3장 과제 목록 459건(국방전략기술 분야 포함), 부록 과제카드 461건 |

## PDF 텍스트 변환

`tools/pdf2text.html`을 브라우저에서 열면 PDF를 pdftotext `-layout`과 같은 형식의 텍스트로 변환합니다(파일은 브라우저 밖으로 전송되지 않음).
변환한 텍스트를 `data/source/full/`에 `YYYY_YY-YY_국방기술기획서_일반본.full.txt` 이름으로 넣고 아래 빌드를 실행하면 반영됩니다.
poppler가 설치된 환경에서는 `scripts/convert_pdfs.sh <PDF 폴더>`로 같은 결과를 얻을 수 있습니다.

## 빌드

```bash
python3 scripts/parse_2022.py            # Drive 텍스트: '22-'36 제2장
python3 scripts/parse_2023.py            # Drive 텍스트(참고용)
python3 scripts/parse_2024.py            # Drive 텍스트: '24-'38 제2장
python3 scripts/parse_2025_ch3.py        # Drive 텍스트(참고용)
python3 scripts/parse_2025_ch2.py        # Drive 텍스트: '25-'39 제2장
python3 scripts/parse_2026.py            # Drive 텍스트(참고용)
python3 scripts/parse_full_lists.py      # 전문: '23~'26 제3장 과제 목록
python3 scripts/parse_full_cards.py      # 전문: '23~'26 부록 과제카드
python3 scripts/parse_full_2026_ch2.py   # 전문: '26-'40 제2장 기술트리
python3 scripts/parse_full_2023_ch2.py   # 전문: '23-'37 제2장 국방기술·과제
python3 scripts/build_inventory.py       # data/inventory.json, inventory.csv, taxonomy.json, stats.json 생성
```

표준 라이브러리만 사용하며, GitHub Actions 배포 시에도 같은 순서로 다시 빌드합니다.

## 유의 사항

- PDF 텍스트 변환 과정에서 표의 열이 섞이거나 줄이 바뀐 경우가 있어 일부 과제명·개요·세부기술명에 오탈자가 남아 있을 수 있습니다.
- 특화연구실 과제카드는 세부과제 표를 포함하고 있어 개요가 세부과제 목록과 섞일 수 있습니다.
- 일반본(공개본)만을 사용했으며, 비밀본의 무기체계 기반 기술확보 전략은 포함하지 않습니다.

## 출처

- 국방기술진흥연구소, 「’22-’36 / ’23-’37 / ’24-’38 / ’25-’39 / ’26-’40 국방기술기획서(일반본)」
- OMB, *2025 Federal Agency AI Use Case Inventory* — Reporting Instructions, Data Dictionary
