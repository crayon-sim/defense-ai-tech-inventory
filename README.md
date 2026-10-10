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
| 대시보드 | 과제 수·상태·예산 요약, 분야별 / 사업구분별 / 기획서 연도별 분포, 인공지능 분야 국방전략기술별 과제, ’26-’40 인공지능 기술개발소요(Lv.4) 집계 |
| 과제 인벤토리 | 1행 1과제 표. 검색·분야·국방전략기술·사업구분·상태·수록 연도 필터, 정렬, 과제 상세(연도별 수록 내역·변경 사항), CSV/JSON 다운로드 |
| 국방전략기술 체계 | 10대 분야 → 30개 국방전략기술(Lv.1) → 세부기술(Lv.2) → 구성기술(Lv.3, 인공지능은 ’26-’40 기술트리)과 연계 과제. ’22-’36 체계(8대 분야 99개 국방전략기술·핵심기술)도 열람 |
| 연도별 변화 | 같은 과제의 사업기간·사업구분·분류·과제명 변경, 최신 과제 목록 미수록 과제 |
| 데이터 안내 | 병합 원칙, 기획서별 추출 범위, OMB 항목 대응표 |

## 데이터

| 파일 | 설명 |
|------|------|
| `data/inventory.json` | 과제별 전체 필드(연도별 이력 `editions`, 변경 사항 `changes` 포함) |
| `data/inventory.csv` | 평면 표(UTF-8 BOM), 1행 1과제 |
| `data/taxonomy.json` | 국방전략기술 체계와 연계 과제, ’22-’36 체계, ’26-’40 인공지능 Lv.4 집계 |
| `data/stats.json` | 대시보드용 집계 |
| `data/DATA_DICTIONARY.md` | 필드 정의와 OMB 항목 대응 |
| `data/source/` | 기획서별 추출 텍스트(원문 PDF에서 변환) |
| `data/intermediate/` | 기획서별 파싱 결과 |

현재 수록 규모(2026-10 기준): 고유 과제 1,020건(’25-’39 과제 목록 644건 전체 포함), 국방전략기술 연계 과제 518건, 인공지능 분야 37건.

### 병합 원칙 — 최신자료 우선

1. 같은 과제가 여러 기획서에 실린 경우, 과제명·사업구분·기간·주관형태·예산·국방전략기술 분류는 **가장 최신 기획서**의 값을 쓴다.
2. 과제번호는 발간 연도마다 다시 매겨지므로 연도별 번호는 `editions.{연도}.project_no`에 보관하고, 사이트 식별자 `KDTI-####`를 별도로 부여한다.
3. 과제 동일성은 과제명을 정규화(공백·기호 제거)해 판정하고, 명칭이 크게 바뀐 과제는 `scripts/build_inventory.py`의 `RENAMED_PROJECTS` 표로 수동 연결한다.
4. 상태(착수 예정 · 진행 중 · 종료)는 2026년을 기준으로 사업기간에서 산출하고, 기획서에 명시된 진행과제/예정과제 표기는 이력으로 보관한다.
5. 최신 과제 목록(’25-’39)에 없는 과거 과제는 삭제하지 않고 "최신 과제 목록 미수록"으로 표시한다.

### 기획서별 추출 범위

원문 PDF(권당 20~32MB)는 Google Drive 연동으로 본문 앞부분만 텍스트로 변환할 수 있었습니다.

| 기획서 | 추출 범위 |
|--------|-----------|
| ’22-’36 | 제2장 8대 분야 99개 국방전략기술 · 핵심기술 목록과 반영과제(590건) |
| ’23-’37 | 제2장 10대 분야 중 7개 분야(인공지능~사이버·네트워크 일부)의 국방기술 목록과 진행·예정과제(232건) |
| ’24-’38 | 제2장 10대 분야 30개 국방전략기술별 과제 목록 전체 + 제3장 기초연구 과제 목록 81건(433건) |
| ’25-’39 | 제2장 전체(30개 국방전략기술·92개 세부기술·연계 과제 377건) + 제3장 과제 목록 전체 644건(과제번호·기간·주관형태·예산) |
| ’26-’40 | 제1장 총론, 제2장 인공지능 분야 전체(Lv.1~Lv.3 기술트리 + 기술개발소요 로드맵), 유·무인 복합 일부. 제3장 과제 목록은 미반영 |

전체 PDF 텍스트(`pdftotext -layout` 결과, 또는 `tools/pdf2text.html`을 브라우저에서 열어 변환한 결과)를 `data/source/`의 같은 파일명으로 교체하고 아래 빌드를 다시 실행하면, 같은 파서로 나머지 장(제3장 과제 목록, 부록 과제카드)까지 확장할 수 있습니다.

## 빌드

```bash
python3 scripts/parse_2022.py
python3 scripts/parse_2023.py
python3 scripts/parse_2024.py
python3 scripts/parse_2025_ch3.py
python3 scripts/parse_2025_ch2.py
python3 scripts/parse_2026.py
python3 scripts/build_inventory.py     # data/inventory.json, inventory.csv, taxonomy.json, stats.json 생성
```

표준 라이브러리만 사용하며, GitHub Actions 배포 시에도 같은 순서로 다시 빌드합니다.

## 유의 사항

- PDF 표 추출 과정에서 열이 섞인 경우가 있어 일부 과제명·세부기술명에 오탈자가 남아 있을 수 있습니다.
- ’26-’40 기획서는 인공지능 분야 기술체계만 반영되어, 과제 목록의 최신 기준은 ’25-’39 기획서입니다.
- 일반본(공개본)만을 사용했으며, 비밀본의 무기체계 기반 기술확보 전략은 포함하지 않습니다.

## 출처

- 국방기술진흥연구소, 「’22-’36 / ’23-’37 / ’24-’38 / ’25-’39 / ’26-’40 국방기술기획서(일반본)」
- OMB, *2025 Federal Agency AI Use Case Inventory* — Reporting Instructions, Data Dictionary
