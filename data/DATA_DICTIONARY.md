# 데이터 사전 (Data Dictionary)

OMB 「2025 Federal Agency AI Use Case Inventory」의 `Validation/data_dictionary.md` 형식을 따라, 본 인벤토리의 열(필드)을 정의한다.
한 행은 하나의 국방기술과제이다. 값은 해당 과제가 수록된 **가장 최신 국방기술기획서**를 기준으로 한다.

파일: `data/inventory.json`(`projects[]`), `data/inventory.csv`(평면 표, UTF-8-SIG)

| # | 필드 | 유형 | OMB 대응 항목 | 설명 |
|---|------|------|---------------|------|
| 1 | `inventory_id` | structured_text | Use Case ID | 사이트 고유 식별자 `KDTI-####`. ’26-’40 과제번호 순, 그다음 ’25-’39 과제번호 순, 이후 기타 과제 순으로 부여. 기획서 과제번호는 매년 재부여되므로 식별자로 쓰지 않는다. |
| 2 | `name` | free_text | Use Case Name | 과제명(최신 기획서 표기). |
| 3 | `name_variants` | list | — | 연도별로 달랐던 과제명 표기. |
| 4 | `program_type` | multiple_choice | Bureau / Component | 사업구분: 기초연구 · 응용연구 · 응용/시험 · 시험개발 · 무기체계 패키지형 · 선도형 핵심기술 · 핵심SW · 선행핵심기술 · 국제공동기술개발 · 미래도전국방기술 · 민·군기술협력 |
| 5 | `program_subtype` | multiple_choice | Bureau / Component | 세부 사업구분: 개별기초 · 특화연구실 · 특화연구센터 · 국방협업 · 국방선행 · PM기획 · 개별과제 · 가교적 연구 · 기술경진대회 |
| 6 | `lead_type` | multiple_choice | Contracting Usage | 주관형태: 산학연 · 국과연 · 정출연 · 국/산 · 미정 |
| 7 | `start_year` | integer | Date Initiated | 착수년도(’26-’40 목록의 "2027년 이후" 표기는 `editions.2026.tbd_years=true`) |
| 8 | `end_year` | integer | Date Deployed(종료 예정) | 종료년도 |
| 9 | `duration_months` | integer | — | 사업기간(개월) |
| 10 | `budget_100m_krw` | number | — | 예산(억원) |
| 11 | `field` | multiple_choice | Topic Area | 10대 국방전략기술 분야: 인공지능 · 유·무인 복합 · 양자 · 우주 · 에너지 · 첨단소재 · 사이버·네트워크 · 센서·전자기전 · 추진 · WMD 대응. ’26-’40 과제 목록의 분야 열 기준(없으면 과거 제2장 연계). 값이 없으면 국방전략기술과 연계되지 않은 과제 |
| 12 | `strategic_tech` | multiple_choice | Topic Area | 30개 국방전략기술(Level 1). ’25-’39 제2장 기준(없으면 ’24-’38, ’23-’37) |
| 13 | `sub_tech` | free_text | Topic Area | 세부기술(Level 2) |
| 14 | `strategic_tech_note` | free_text | — | 과거 제2장 분류의 분야와 최신 분야가 다른 경우의 안내 |
| 15 | `weapon_system_field` | multiple_choice | Topic Area | 과제카드의 무기체계 분야(지휘통제·통신 · 감시·정찰 · 기동 · 함정 · 항공 · 화력 · 방호 · 사이버 · 우주 · 기타) |
| 16 | `tech_field` | multiple_choice | Topic Area | 과제카드의 기술 분야(센서 및 제어 · 정보통신 · 기계 · 탄약/에너지 · 소재 · 화생방 등, 연도에 따라 분류명이 다름) |
| 17 | `legacy_2022_field` / `legacy_2022_tech` | free_text | — | ’22-’36 기획서의 8대 분야 / 99개 국방전략기술 |
| 18 | `linked_core_techs` | list | Problem Solved | 과제가 확보하는 핵심기술(’22-’36) · 국방기술(’23-’37) 명칭 |
| 19 | `status` | multiple_choice | Development Stage | 2026년 기준 사업기간으로 산출: 착수 예정(착수년도 > 2026) · 진행 중 · 종료(종료년도 < 2026) |
| 20 | `status_note` | free_text | Retired | 최신 과제 목록(’26-’40)에 수록되지 않은 과제에 대한 안내 |
| 21 | `in_latest_master_list` | boolean | — | ’26-’40 기획서 제3장 과제 목록 수록 여부 |
| 22 | `first_edition` / `latest_edition` / `editions_listed` | year | Previously Reported | 처음·마지막 수록 기획서 연도, 수록 연도 목록 |
| 23 | `editions` | object | — | 연도별 수록 내역: `project_no` · `stage`(사업구분 원문) · `period` · `start_year` · `end_year` · `duration_months` · `lead_type` · `budget_100m_krw` · `field` · `strategic_tech` · `sub_tech` · `status_tag`(’23-’37의 진행과제/예정과제) · `core_techs` · `card`(과제카드: `desc` · `research_items` · `weapon_system_field` · `tech_field` · `phase_periods`) · `source` |
| 24 | `changes` | list | — | 연속한 두 기획서 사이의 변경: `item`(사업기간 · 사업구분 · 과제번호 · 국방전략기술 · 세부기술 · 국방전략기술 분야 · 예산(억원) · 주관형태 · 과제명), `before`, `after` |
| 25 | `description` | free_text | Problem Solved | 과제카드 개요(가장 최신 과제카드 기준) |
| 26 | `research_items` | free_text | System Outputs | 과제카드 연구항목 |
| 27 | `phase_periods` | list | — | 응용/시험 연계 과제의 단계별 기간(응용 / 시험) |

## taxonomy.json

- `fields[]` — 10대 분야(`name`, `projects[]`, `lv4_summary_2026`) → `techs[]`(30개 국방전략기술: `name`, `desc`, `desc_source`, `projects[]`, `defense_techs_2023[]`) → `subs[]`(세부기술: `code`, `name`, `desc`, `desc_source`, `desc_2025`, `lv3[]`, `projects[]`). `subs`/`lv3`는 ’26-’40 기획서 기술트리(Lv.2/Lv.3)이며, ’25-’39 세부기술 정의를 `desc_2025`로 덧붙인다.
- `defense_techs_2023[]` — ’23-’37 기획서의 국방기술(`name`, `desc`, `projects[]`).
- `legacy_2022.fields[]` — ’22-’36 기획서의 8대 분야 → 99개 국방전략기술 → 핵심기술(`core_techs[]`: `name`, `desc`, `projects[]`).
- `lv4_summary_2026` — ’26-’40 분야별 기술개발소요(Lv.4)의 확보시기·사업추진방안·확보여부 집계(텍스트 패턴 집계).

## 값 정규화

- 사업구분 표기는 연도마다 달라(예: `응용`/`응용연구`, `패키지형`/`국방협업`) `program_type`·`program_subtype`로 통일했다. 원문 표기는 `editions.{연도}.stage`에 남긴다.
- 분야명 표기(`유무인 복합`/`유·무인 복합`, `사이버네트워크`/`사이버·네트워크` 등)는 10대 분야 명칭으로 통일했다.
- ’23-’37 제3장 과제 목록은 사업구분별로 순번이 다시 시작하므로, 같은 판의 부록 과제카드(전역 번호)와 과제명으로 대조해 `project_no`를 복원했다(복원 불가 시 비움).
- 과제 동일성은 과제명에서 공백·기호를 제거한 문자열의 일치(또는 90% 이상 유사)로 판정했고, 명칭이 크게 바뀐 과제는 `scripts/build_inventory.py`의 `RENAMED_PROJECTS` 표로 수동 연결했다.
