# 데이터 사전 (Data Dictionary)

OMB 「2025 Federal Agency AI Use Case Inventory」의 `Validation/data_dictionary.md` 형식을 따라, 본 인벤토리의 열(필드)을 정의한다.
한 행은 하나의 국방기술과제이다. 값은 해당 과제가 수록된 **가장 최신 국방기술기획서**를 기준으로 한다.

파일: `data/inventory.json`(`projects[]`), `data/inventory.csv`(평면 표, UTF-8-SIG)

| # | 필드 | 유형 | OMB 대응 항목 | 설명 |
|---|------|------|---------------|------|
| 1 | `inventory_id` | structured_text | Use Case ID | 사이트 고유 식별자 `KDTI-####`. ’25-’39 기획서 과제번호 순, 이후 기타 과제 순으로 부여. 기획서 과제번호는 매년 재부여되므로 식별자로 쓰지 않는다. |
| 2 | `name` | free_text | Use Case Name | 과제명(최신 기획서 표기). |
| 3 | `name_variants` | list | — | 연도별로 달랐던 과제명 표기. |
| 4 | `program_type` | multiple_choice | Bureau / Component | 사업구분: 기초연구 · 응용연구 · 응용/시험 · 시험개발 · 무기체계 패키지형 · 선도형 핵심기술 · 핵심SW · 선행핵심기술 · 국제공동기술개발 · 미래도전국방기술 · 민·군기술협력 |
| 5 | `program_subtype` | multiple_choice | Bureau / Component | 세부 사업구분: 개별기초 · 특화연구실 · 특화연구센터 · 국방협업 · 국방선행 · PM기획 · 개별과제 |
| 6 | `lead_type` | multiple_choice | Contracting Usage | 주관형태: 산학연 · 국과연 · 정출연 · 국/산 · 미정 |
| 7 | `start_year` | integer | Date Initiated | 착수년도 |
| 8 | `end_year` | integer | Date Deployed(종료 예정) | 종료년도 |
| 9 | `duration_months` | integer | — | 사업기간(개월). ’25-’39 과제 목록에만 수록 |
| 10 | `budget_100m_krw` | number | — | 예산(억원). ’25-’39 과제 목록 및 ’24-’38 기초연구 목록에 수록 |
| 11 | `field` | multiple_choice | Topic Area | 10대 국방전략기술 분야: 인공지능 · 유·무인 복합 · 양자 · 우주 · 에너지 · 첨단소재 · 사이버·네트워크 · 센서·전자기전 · 추진 · WMD 대응. 값이 없으면 국방전략기술과 연계되지 않은 과제(제3장 목록에만 수록) |
| 12 | `strategic_tech` | multiple_choice | Topic Area | 30개 국방전략기술(Level 1) |
| 13 | `sub_tech` | free_text | Topic Area | 세부기술(Level 2) |
| 14 | `legacy_2022_field` | multiple_choice | — | ’22-’36 기획서의 8대 국방전략기술 분야 |
| 15 | `legacy_2022_tech` | free_text | — | ’22-’36 기획서의 국방전략기술(99개) |
| 16 | `linked_core_techs` | list | Problem Solved | 과제가 확보하는 핵심기술(’22-’36) · 국방기술(’23-’37) 명칭 |
| 17 | `status` | multiple_choice | Development Stage | 2026년 기준 사업기간으로 산출: 착수 예정(착수년도 > 2026) · 진행 중 · 종료(종료년도 < 2026) |
| 18 | `status_note` | free_text | Retired | 최신 과제 목록(’25-’39)에 수록되지 않은 과제에 대한 안내 |
| 19 | `in_latest_master_list` | boolean | — | ’25-’39 기획서 제3장 과제 목록(644건) 수록 여부 |
| 20 | `first_edition` / `latest_edition` | year | Previously Reported | 처음·마지막으로 수록된 기획서 연도 |
| 21 | `editions_listed` | list | Previously Reported | 수록 기획서 연도 목록 |
| 22 | `editions` | object | — | 연도별 수록 내역: `project_no`(과제번호) · `stage`(사업구분 원문 표기) · `period`(기간) · `field`/`strategic_tech`/`sub_tech`(분류) · `status_tag`(’23-’37의 진행과제/예정과제) · `budget_100m_krw` · `core_techs` · `source` |
| 23 | `changes` | list | — | 연속한 두 기획서 사이의 변경: `item`(사업기간 · 사업구분 · 과제번호 · 국방전략기술 · 세부기술 · 과제명), `before`, `after` |
| 24 | `description` / `research_items` | free_text | Problem Solved / System Outputs | 과제카드의 개요·연구항목(부록이 추출된 범위에 한해 수록, 현재는 비어 있음) |

## taxonomy.json

- `fields[]` — 10대 분야 → `techs[]`(30개 국방전략기술: `name`, `desc`, `desc_source`, `projects[]`) → `subs[]`(세부기술: `code`, `name`, `desc`, `desc_source`, `desc_2025`, `lv3[]`, `projects[]`). 인공지능 분야의 `subs`/`lv3`는 ’26-’40 기획서 기술트리(Lv.2/Lv.3)이다.
- `legacy_2022.fields[]` — ’22-’36 기획서의 8대 분야 → 99개 국방전략기술 → 핵심기술(`core_techs[]`: `name`, `desc`, `projects[]`).
- `ai_lv4_summary_2026` — ’26-’40 인공지능 분야 기술개발소요(Lv.4)의 확보시기·사업추진방안·확보여부 집계.

## 값 정규화

- 사업구분 표기는 연도마다 달라(예: `응용`/`응용연구`, `패키지형`/`국방협업`) `program_type`·`program_subtype`로 통일했다. 원문 표기는 `editions.{연도}.stage`에 남긴다.
- 분야명 표기(`유무인 복합`/`유·무인 복합`, `사이버네트워크`/`사이버·네트워크` 등)는 10대 분야 명칭으로 통일했다.
- 과제 동일성은 과제명에서 공백·기호를 제거한 문자열의 일치(또는 90% 이상 유사)로 판정했고, 명칭이 크게 바뀐 과제는 `scripts/build_inventory.py`의 `RENAMED_PROJECTS` 표로 수동 연결했다.
