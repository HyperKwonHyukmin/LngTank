# GTT Mark III 주름(Waffle) LNG 멤브레인 — 3D CAD 산출물 (v2)

**US Patent 3,199,963** — B. G. Bengtsson, *"Corrugated Sheet Formed Material"* (1962 출원 / 1965 등록).
GTT Technigaz **Mark III** 화물창 시스템의 1차 방벽(primary corrugated membrane)으로 상용화된 "와플(waffle)"
주름 스테인리스 멤브레인을, **실 Mark III 스펙 실측치**를 부여해 3D로 파라메트릭하게 재현한 결과물입니다.

> **v2 — Mark III 충실도 업그레이드**: 워크플로 종합검토(웹 실측 + 코드 감사)를 반영해 ① **이중높이 주름**
> ② **법선방향 일정두께** ③ 사실적 오메가형 단면 ④ 표준 패널 모드 ⑤ 다중 포맷 export 를 적용했습니다.

🌐 **라이브 3D 뷰어**: https://hyperkwonhyukmin.github.io/LngTank/

## 적용 치수 (mm) — 출처 실측

| 파라미터 | 값 | 근거 |
|---|---|---|
| 주름 피치 `P` (정사각 격자) | **340** | 확정 (GTT ISOPE Bogaert 2010) |
| 시트 두께 `t` (304L) | **1.2** | 확정 |
| **큰 주름 높이** `H_large` | **54** | **확정** (큰 주름이 작은 주름 위로 타고 넘어감) |
| **작은 주름 높이** `H_small` | **37.2** | **확정** |
| 노드(knot) 높이 | **≈ 54** | 확정 (큰 주름 높이가 지배) |
| 표준 시트 | 1020 × 3060 (3×9 셀) | 확정 (≈ 1 m × 3 m) |

형상: 두 직교 방향의 **크기가 다른** 주름이 교차하며, 큰 주름이 작은 주름 위를 지나가는 지점에 knot 형성.
knot 접힘이 −163 °C LNG의 **양방향(biaxial) 열수축**을 흡수하는 것이 발명 요지(출처: UCL/Paik FE).

## 파일

| 파일 | 내용 |
|---|---|
| `waffle_membrane.py` | numpy+trimesh **일정두께 1.2 mm 박막 멤브레인** (height-field, **법선오프셋**) → STL/OBJ/GLB |
| `waffle_cad_step.py` | CadQuery **파라메트릭 B-rep 솔리드 릴리프 마스터** → STEP/IGES/BREP/STL |
| `waffle_knot.py` | **접힌 'mushroom' 노드**(오버행 + 4-fold 크리스 + 플레어) 명시적 솔리드 → STL/GLB |
| `waffle_preview.html` | 의존성-경량 **Three.js 인터랙티브 뷰어** (GitHub Pages 배포) |
| `waffle_membrane.{stl,obj,glb}` | 박막 멤브레인 메시 (mm) |
| `waffle_membrane.{step,igs,brep}` | CAD B-rep 솔리드 릴리프 마스터 (FreeCAD/Fusion/SolidWorks/CAE) |
| `waffle_membrane_thin.{step,igs,brep}` | **일정두께 1.2 mm 박막 B-rep** (`--thin`, OCCT shell) |
| `waffle_knot_thin.{stl,glb}` | **접힘 노드 일정두께 박막 시트** (`--thin`, 법선오프셋) |
| `waffle_render_thin.png` | **박막 단면 검증 렌더** (이중 스킨 1.2 mm 가시화) |
| `waffle_render_*.png` | 정적 미리보기 렌더 |

## 실행

```bash
pip install numpy trimesh cadquery
python waffle_membrane.py            # 3×3 셀 (1020×1020)
python waffle_membrane.py --panel    # 표준 스트레이크 3×9 (1020×3060)
python waffle_cad_step.py            # 솔리드 릴리프 마스터 → STEP/IGES/BREP/STL
python waffle_cad_step.py --thin     # 일정두께 1.2 mm 박막 B-rep (OCCT shell)
python waffle_cad_step.py --panel    # 표준 스트레이크
python waffle_knot.py                # 접힌 'mushroom' 노드 솔리드 → STL/GLB
python waffle_knot.py --thin         # 접힘 노드 일정두께 박막 시트 → STL/GLB
python waffle_render_thin.py         # 박막 단면 검증 렌더
python waffle_render_knot.py         # 접힘 노드 3-뷰 검증 렌더
```

뷰어: `waffle_preview.html` 더블클릭(또는 위 라이브 URL). 드래그=회전, 스크롤=확대.
컨트롤 — **N×N 슬라이더**, **Folded knots**(교차점마다 접힘 노드 실제 배치), **Panel 3×9** 버튼,
**Height colormap**(높이별 색), 베이스 그리드(340 mm), 와이어프레임.
*(Three.js를 CDN에서 로드 — 인터넷 필요. 실패 시 안내 메시지 표시)*

## v2에서 개선된 점 (Mark III 감사 반영)

- **이중높이 주름** — 단일 34 mm → 실제 大 54 / 小 37.2 mm. knot가 큰 주름 높이에 자동 정렬.
- **법선방향 일정두께** — 바닥면을 수직(−z)이 아닌 **표면 법선** 방향으로 오프셋. 경사면(최대 ~41°)에서
  수직오프셋 시 두께가 `t·cos θ ≈ 0.9 mm`로 얇아지던 문제를 해소, 전 영역 1.2 mm 유지.
- **사실적 단면** — 코사인 → 평탄밸리 + 직선플랭크 + 평탄크레스트(오메가형 근사, `VALLEY/CREST` 파라미터).
- **표준 패널** — `--panel`로 3×9 스트레이크(1020×3060) 생성.
- **CAD 품질** — argparse·`build()` API·**유효 단일 솔리드 검증**·**STEP/IGES/BREP/STL 다중 export**·문서화된 리브 단면.
- **뷰어** — 스케일 그리드/캡션, 높이 컬러맵, 패널 프리셋, 오프라인 에러 핸들러, 근사 고지문.

## 두 모델의 차이 & 남은 한계

- **`waffle_membrane.*` (height-field 메시)** = 기하학적으로 충실한 **일정두께 1.2 mm 박막**. watertight 검증됨.
  시각화·3D프린트·FE 시드에 적합.
- **`waffle_membrane.step/.igs/.brep` (CadQuery)** = 편집 가능한 **B-rep 솔리드 릴리프 마스터**(속이 찬 양각).
  CAD 부울·도면화에 적합.
- **`waffle_knot.py` (접힘 노드)** = height-field가 **원천적으로 표현 못하는** knot의 **오버행(re-entrant)
  · 4-fold 크리스 · mushroom 플레어**를 명시적 솔리드로 구현(watertight). 발명 요지인 fold 거동을 시각화·검토용으로 제공.
- **✅ 뷰어 통합 완료**: `waffle_preview.html`의 **Folded knots** 토글 — 교차점마다 접힘 노드를
  InstancedMesh로 배치하고 높이장에 well(함몰)을 적용해 자연스럽게 안착. 주름이 knot 사이를 잇는
  실제 Mark III 패턴을 인터랙티브로 확인 가능.
- **✅ 일정두께 박막 B-rep 완료 (항목 ①)**: `waffle_cad_step.py --thin` → 멤브레인을 OCCT shell로 속을 비워
  **유효 1.20 mm 일정두께 벽**의 단일 유효 솔리드 B-rep(STEP/IGES/BREP) 생성(3×3·3×9 패널 검증).
  접힘 노드는 재진입(re-entrant) 플리트 때문에 OCCT shell이 불가(StdFail_NotDone) → `waffle_knot.py --thin`
  으로 **표면 법선 오프셋 + 림 밴드 봉합**(부울 엔진 불필요)을 써서 watertight 1.2 mm 접힘 시트로 구현.
- **✅ 근수직 플랭크 B-rep 완료 (항목 ②)**: 리브 단면을 **가파른 단조(monotonic) 사다리꼴(80° 플랭크)**로 교체.
  아크 필렛(오메가형)은 중간 플랭크가 바깥으로 부풀어(barrel) 내향 오프셋을 깨뜨리므로 제외 — 같은 80° 근수직
  이면서 **shell 가능**한 형상으로 통일(솔리드·박막 모두 검증). 단면 검증은 `waffle_render_thin.png` 참조.
- **✅ 접힘 노드 제조-충실도 향상 (항목 ③)**: 공개 문헌(Paik/UCL FE, Bengtsson 특허, GTT)에서 **확인된 사실을
  모델에 반영**하고, 노드 치수를 **실제 주름 스펙에서 유도(derive)**해 매직넘버를 제거했습니다.
  `waffle_render_knot.py` → `waffle_render_knot.png` 로 검증.

  | 구분 | 내용 |
  |---|---|
  | **확인·반영(confirmed)** | knot = **大·小 주름의 교차점**(Paik/UCL "intersection of small and large corrugations"); 정점高 = **큰 주름 크레스트 54 mm**(큰 주름이 작은 주름 위로 연속 통과); 주름보다 **덜 변형되는 단단한 'folded structure'**, 외력 시 **완전히 펴지며 reserve length 방출**(GTT); **4-fold** 교차(두 주름 축 방향 arm) + "short/long pressing indentations" |
  | **유도(derived, 매직넘버 제거)** | `H_N=54`(=큰 크레스트), `R_BASE=77.3`(=大·小 주름 footprint 합), `R_CAP=39.8`(=큰 크레스트 평탄폭×1.3), `Z_WAIST=0.69`(**허리=작은 크레스트 높이 37.2 mm**, 즉 tuck 위치), 2-fold 비대칭(x=192>y=157: 큰 arm>작은 arm) |
  | **여전히 근사(proprietary)** | GTT의 **정확한 프레스 금형 fold 단면** — 비공개. 플리트 진폭/트위스트/쿠션 계수는 *문헌 기반 근사*. |

  출처: Paik et al. *"Nonlinear structural behaviour of membrane-type LNG carrier"* (UCL discovery 1535317);
  Bengtsson **US 3,199,963**; GTT Mark III 시스템 자료.

*세부 배경·방법 비교·치수 근거는 검토 워크플로 산출 보고서 참조.*
