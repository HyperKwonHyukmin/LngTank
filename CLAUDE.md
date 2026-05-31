# CLAUDE.md — 프로젝트 핸드오프 / 작업 컨텍스트

> 이 파일은 Claude Code가 세션 시작 시 자동 로드합니다. 다른 Claude Code 인스턴스가
> 이 프로젝트의 **현재 상태·핵심 결정·함정**을 빠르게 파악하도록 작성된 오리엔테이션
> 문서입니다. 사용자 대상 설명은 `README.md`, 배경/방법 비교는 README를 참조하세요.

## 한 줄 요약
**GTT Mark III LNG 화물창 1차 방벽(주름 "와플" 멤브레인, Bengtsson US 3,199,963)** 을
실측 스펙으로 **파라메트릭 3D 재현**하는 프로젝트. 산출물 = ① numpy/trimesh 박막 메시,
② CadQuery B-rep 솔리드/박막, ③ 접힘 노드(knot) 명시적 솔리드/박막, ④ Three.js 웹 뷰어
(GitHub Pages 배포). 단위 = **mm**.

## 진행 상태 (2026-05-31 기준)
워크플로 종합검토에서 도출된 **고도화 항목 ①②③ 모두 완료**.

- **① 일정두께 박막 B-rep** — `waffle_cad_step.py --thin` (멤브레인, OCCT shell) +
  `waffle_knot.py --thin` (접힘 노드, trimesh 법선오프셋). ✅
- **② 근수직(80°) 플랭크 B-rep** — 리브 단면을 가파른 단조 사다리꼴로 교체. ✅
- **③ 접힘 노드 제조-충실도** — 노드 치수를 실제 주름 스펙에서 유도(매직넘버 제거),
  문헌 확인 사실 반영. 정확한 프레스 fold는 GTT 비공개라 *문헌 기반 근사*로 명시. ✅

## 확정 스펙 (mm) — 웹 실측 근거
| 파라미터 | 값 | 근거 |
|---|---|---|
| 주름 피치 `P` (정사각 격자) | **340** | GTT ISOPE Bogaert 2010 |
| 시트 두께 `t` (304L SUS) | **1.2** | 확정 |
| 큰 주름 높이 `H_LARGE` | **54** | 확정 (큰 주름이 작은 주름 위로 연속 통과) |
| 작은 주름 높이 `H_SMALL` | **37.2** | 확정 |
| 노드(knot) 정점 높이 | **= 54** | 큰 주름 크레스트 지배 |
| 표준 시트 | 1020 × 3060 (3×9 셀) | ≈ 1 m × 3 m |
| 플랭크 각 (근수직) | **80°** | 설계 선택(근수직), shell 가능하도록 |

공유 단면 파라미터: `CRESTF=0.09`(크레스트 평탄 반폭/P), height-field 쪽은 추가로
`VALLEY=0.27`, `P_NORM=8`(softmax 지수).

## 파일 맵
### 스크립트 (모두 `python <file>` 실행, argparse 지원)
| 파일 | 역할 | 주요 플래그 |
|---|---|---|
| `waffle_membrane.py` | numpy+trimesh **height-field 박막**(법선오프셋 1.2 mm) → STL/OBJ/GLB | `--panel`(3×9) |
| `waffle_cad_step.py` | CadQuery **B-rep**: 솔리드 릴리프 마스터 / 박막 → STEP/IGES/BREP/STL | `--thin`, `--panel`, `--nx/--ny`, `--wall` |
| `waffle_knot.py` | **접힘 노드**(명시적 솔리드 / 박막 시트) → STL/GLB | `--thin`, `--nt/--nz`, `--wall` |
| `waffle_render_thin.py` | 박막 **단면 검증** 렌더 → `waffle_render_thin.png` | — |
| `waffle_render_knot.py` | 접힘 노드 **3-뷰** 렌더 → `waffle_render_knot.png` | — |
| `waffle_preview.html` | **Three.js 인터랙티브 뷰어**(CDN importmap). 배포 원본 | — |

### 출력물 (생성됨, 재생성 가능)
- 멤브레인 솔리드: `waffle_membrane.{step,igs,brep}`, `waffle_membrane_cad.stl`, `.{stl,obj,glb}`
- 멤브레인 박막: `waffle_membrane_thin.{step,igs,brep}`, `waffle_membrane_thin_cad.stl`
- 노드: `waffle_knot.{stl,glb}`(솔리드), `waffle_knot_thin.{stl,glb}`(박막)
- 렌더: `waffle_render_{heightfield,cadquery,knot,thin}.png`

### 배포본
- `waffle-site/index.html` = `waffle_preview.html` 사본. **별도 git repo**(아래 배포 섹션).

## 핵심 기술 결정 & 함정 (반드시 숙지)
1. **이중높이 height-field**: `z = softmax_p(H_LARGE·ridge(y), H_SMALL·ridge(x))`,
   `ridge`는 사다리꼴 단면(평탄밸리+직선플랭크+평탄크레스트). 큰 주름은 y에, 작은 주름은 x에 의존.
2. **법선방향 일정두께**: 바닥을 −z가 아닌 **표면 법선** 방향으로 오프셋. 수직오프셋이면
   경사면에서 `t·cosθ`로 얇아짐(41°→0.9 mm). 법선오프셋은 전 영역 1.2 mm 유지.
3. **⚠️ omega(아크 필렛) 단면 vs OCCT shell = 양립 불가**. 아크 필렛을 넣으면 중간 플랭크가
   바깥으로 부풀어(barrel) **단면이 비단조(non-monotonic)** → OCCT 내향 오프셋이 자기교차로
   실패(`StdFail_NotDone`). **해결 = 가파른 단조 사다리꼴**(80°, 아크 없음, `Wf=Wc+h/tan(80°)`).
   근수직이면서 shell 가능. `waffle_cad_step.py`의 `flank_profile()` 가 이 형상.
   → **리브 단면에 아크 필렛/오메가를 다시 도입하면 `--thin`이 깨진다. 하지 말 것.**
4. **⚠️ 접힘 노드는 OCCT shell 불가**(재진입 플리트 → `StdFail_NotDone`). 그래서 노드 박막은
   **trimesh 법선오프셋 + 바닥 림 밴드 봉합**(`knot_thin_mesh`, 부울 엔진 불필요)으로 구현.
   manifold/blender/openscad 같은 부울 엔진에 의존하지 않음 — 순수 numpy/trimesh.
5. **노드 치수는 모두 유도값**(`waffle_knot.py` 상단). 매직넘버 금지:
   `H_N=H_LARGE`, `R_BASE=WF_L+WF_S=77.3`, `R_CAP=WC·1.3=39.8`,
   `R_WAIST=R_CAP−0.6·(H_LARGE−H_SMALL)=29.7`, `Z_WAIST=H_SMALL/H_LARGE=0.69`(허리=작은 크레스트
   높이=tuck 위치), `ASYM=0.10`(2-fold: 큰 arm>작은 arm), `FOLD_PHASE0=π/2`(fold를 주름 축에 정렬).
6. **노드 = 大·小 주름 교차점**(Paik/UCL FE 확정). 큰 주름이 연속으로 위를 지나가고, 작은 주름이
   파고든다. 노드는 주름보다 **덜 변형되는 단단한 folded structure**. 정확한 프레스 fold는 비공개.
7. **뷰어 노드는 JS 포트**(`waffle_preview.html`의 `buildKnotGeometry`). Python `waffle_knot.py`와
   **동일 유도값**을 유지해야 함(`RB=77.3, RW=29.7, RC=39.8, ZW=0.689, PHASE0=π/2, ASYM=0.10`).
   Python 노드를 바꾸면 JS도 같이 바꾸고 재배포.
8. **검증 기준**: 멤브레인 B-rep = `check_solid()`(단일·isValid·vol>0). 노드 메시 = `is_watertight`.
   박막 두께 sanity = 2V/A 휴리스틱(크리스/이중스킨에서 약간 저평가됨 — watertight가 1차 기준).

## 실행
```bash
pip install numpy trimesh cadquery matplotlib   # 뷰어 검증 시 playwright 추가
python waffle_membrane.py [--panel]          # height-field 박막
python waffle_cad_step.py                    # 솔리드 릴리프 마스터
python waffle_cad_step.py --thin [--panel]   # 일정두께 1.2 mm 박막 B-rep
python waffle_knot.py                        # 접힘 노드 솔리드
python waffle_knot.py --thin                 # 접힘 노드 박막 시트
python waffle_render_thin.py                 # 박막 단면 검증 렌더
python waffle_render_knot.py                 # 노드 3-뷰 렌더
```
검증된 수치(참고): 멤브레인 박막 3×3 = 단일 유효 솔리드 1020×1020×55.2, vol 1942 cm³, eff 1.20 mm.
패널 3×9 = 1020×3060×55.2, vol 5564 cm³, eff 1.20. 노드 박막 = watertight 192×157×55, eff 1.11 mm.

## 배포 (GitHub Pages) — 뷰어 페이지 **하나만** 공개
- repo: `https://github.com/HyperKwonHyukmin/LngTank.git` (origin)
- live: **https://hyperkwonhyukmin.github.io/LngTank/**
- 작업 디렉터리 `waffle-site/` 가 **별도 git repo**(상위 `C:\Coding\LngTanker` 는 git 아님).
- git user: `HyperKwonHyukmin` / `khm7529@gmail.com`, `credential.helper=manager`(GCM 토큰 저장).
- 배포 절차: `waffle_preview.html` 수정 → `cp waffle_preview.html waffle-site/index.html`
  → `git -C C:/Coding/LngTanker/waffle-site add/commit/push origin main`.
- **사용자 제약**: "이 페이지만"(뷰어 HTML만 공개). 다른 산출물(CAD/메시)은 배포하지 않음.
- 최신 커밋: `194f77a`(노드 regrounding). 이전: `39eef8a`(노드 통합), `5fd09f2`(v2 뷰어).
- Pages CDN 반영은 push 후 **1~2분 지연**. 라이브 확인은 마커 grep(예: `RB = 77.3`).

## 환경 & 도구 함정 (Windows)
- OS=Windows 11, 기본 셸=PowerShell. **Bash 도구도 사용 가능**(POSIX 스크립트용).
- ⚠️ **Bash 도구 작업디렉터리 지속**: 복합 명령의 `cd waffle-site` 가 다음 호출까지 유지됨.
  파일이 "안 보이면" 디렉터리가 바뀐 것 — **절대경로** 또는 `git -C <abs>` 사용 권장.
- ⚠️ **cp949 인코딩**: 한글/em-dash 출력 시 `PYTHONIOENCODING=utf-8` + 스크립트에
  `sys.stdout.reconfigure(encoding="utf-8")`. (모든 스크립트에 이미 적용됨.)
- CadQuery **2.7.0 / OCP(OpenCascade)**. STEP는 schema가 보통 **AP214**로 기록됨
  (AP242 요청해도 OCP 버전에 따라 무시). `.faces("<Z").shell(-t)` = `BRepOffsetAPI_MakeThickSolid`.
- **PDF 읽기**: Read 도구는 `pdftoppm` 필요(이 환경에 없음). 텍스트는 `pypdf`로 추출
  (`fitz/PyMuPDF` 없음). WebFetch는 ScienceDirect 등에서 **403**(페이월) — 공개 PDF만.
- **뷰어 검증(Playwright)**: chromium `--enable-unsafe-swiftshader --use-gl=angle
  --use-angle=swiftshader`, `wait_until="domcontentloaded"` + `screenshot(animations="disabled")`
  (networkidle/무거운 dpr는 타임아웃). 페이지에 `window.__ok===true` 와 `#knots` 토글 존재.
- 임시 파일은 `_` 접두사로 만들고 작업 후 삭제(현재 leftover 없음).

## 남은 한계 / 다음 작업 후보
- **③ 잔여**: GTT의 **정확한 프레스 금형 fold 단면**은 비공개 → 현재 노드 fold는 *문헌 기반 근사*.
  특허/제조 도면 실측이 있어야 manufacturing-exact 가능.
- 노드 박막 eff 두께가 크리스에서 ~1.1 mm로 약간 저평가(법선오프셋의 t·cos(half-crease) 특성).
  필요 시 fold 영역 두께 보정 검토 가능.
- 멤브레인 박막과 접힘 노드 박막은 **현재 분리 산출물**. 단일 통합 박막 솔리드로 부울 결합은 미수행.

## 출처 (공개)
- Paik et al., *Nonlinear structural behaviour of membrane-type LNG carrier* —
  https://discovery.ucl.ac.uk/1535317/ ("knot = intersection of small and large corrugations")
- Bengtsson, **US 3,199,963** — https://patents.google.com/patent/US3199963A/en
- GTT Mark III systems — https://www.gtt.fr/en/technologies/markiii-systems
