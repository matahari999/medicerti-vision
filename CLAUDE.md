# medicerti-vision — Medical Edge Vision AI SaaS

<!-- v1.0 | Medical Facility Intelligent CCTV Analysis Edge SaaS -->

---

## 1. Product Identity

medicerti-vision은 중소 요양병원·요양원 대상 **기존 CCTV 인프라를 활용한 Edge AI 영상 분석 SaaS**입니다. 신규 하드웨어 교체 없이 소프트웨어만 얹어 환자 안전(낙상·이탈·배회) 및 보안(미등록 외부인 감지)을 실시간으로 감지하고, 의료기관 인증평가(Accreditation) 서식을 자동 출력합니다.

---

## 2. Architecture Principles

### 2.1 Network & Deployment
- **On-Premise Edge only:** 모든 영상 분석은 병원 내부망에서 완료. 환자 영상/생체 데이터는 절대 외부 클라우드로 유출 금지
- **Mini Edge AI PC:** NVIDIA RTX GPU 탑재 소형 PC 1대. 대당 원가 100~150만원 수준
- **연결 방식:** 병원 기존 DVR/NVR과 동일 내부 스위치에 LAN 연결, RTSP 스트림만 추출

### 2.2 Stream Protocol
- **Ingress:** RTSP (Real-Time Streaming Protocol) 표준만 사용. ONVIF 호환은 옵션
- **가변 환경 대응:** 컬러/흑백(IR 야간) 모두 기본 상정. RGB 의존성 배제, 명암비(Contrast) + 형태 분석 위주
- **Frame Pipeline:** 멀티스레딩 기반 프레임 드롭 큐(maxsize=3~5)로 Lag Accumulation 방지. 과거 프레임 밀림 현상 차단

### 2.3 Multi-Channel
- **최소 사양:** 4~8채널 병렬 실시간 분석 (단일 GPU 기준)
- **채널 추가 시:** 미니 PC 업그레이드 또는 추가 Edge PC 설치

---

## 3. Core Detection Engine

### 3.1 낙상 및 쓰러짐 감지 (Fall Detection)
- **방식:** Skeleton Joint (머리·어깨·골반·무릎) 17~25개 포인트 실시간 추적
- **임계값:** 척추 중심 관절축이 0.5초 이내에 바닥면과 수평에 가깝게 급격 붕괴 → Fall Event
- **출력:** 이벤트 타임스탬프 + 카메라 ID + 스냅샷 + Bounding Box 좌표

### 3.2 이탈 감지 (Geo-Fencing / Elopement)
- **방식:** 관리자가 대시보드 도면 UI에 가상 폴리곤(Polygon) 경계선 지정
- **임계값:** 환자복 객체가 경계선 통과 → Elopement Alert
- **사전 예방:** 침대에서 일어나 경계선 방향으로 접근 시 Pre-Alert

### 3.3 배회 감지 (Loitering)
- **방식:** 특정 Zone 내 객체 정체 시간 측정
- **임계값:** 30초 이상 동일 구역 목적 없이 정체 → Loitering Event
- **출력:** Zone ID + 체류 시간 로그

### 3.4 미등록 외부인 감지 (Stranger Detection)
- **방식:** 얼굴 특징값 벡터(Face Embedding)와 화이트리스트(직원·상주 보호자) 매칭
- **임계값:** 매칭률 < 설정값(예: 0.7) + 통제 시간(22:00~06:00) + 제한 구역 진입 → Security Alert
- **얼굴 DB:** 로컬 Edge PC 내 암호화 저장. 외부 전송 금지

---

## 4. Privacy & Data Governance

### 4.1 실시간 프라이버시 마스킹
- **평시:** 간호사 관제 모니터에는 원본 영상 대신 실루엣(Silhouette) 또는 Skeleton Line만 렌더링
- **경보 해제:** 낙상/이탈 최종 판정 시에만 해당 카메라 프라이버시 필터 일시 해제 → 의료진 상황 파악
- **모자이크 처리:** 얼굴·신체 노출 부위 자동 블러 처리 옵션

### 4.2 데이터 저장
- **로컬 DB:** SQLite 또는 로컬 PostgreSQL. 모든 이벤트 로그(시간·카메라ID·종류·스냅샷) 유실 없이 적재
- **보관 기간:** 이벤트 스냅샷 최소 1년 이상 (인증평가 증빙 대응)

---

## 5. Digital Zoom & ROI Tracking

### 5.1 소프트웨어 디지털 줌
- **물리적 제약:** 카메라는 고정형(Fixed Stream)으로 상정. 모든 줌은 프레임 행렬(Matrix) 슬라이싱 기반 디지털 크롭
- **자동 추적 줌:** Fall/Loitering 객체의 Bounding Box 중심으로 2~4배율 확대 서브 윈도우를 대시보드에 팝업
- **보간법:** OpenCV `cv2.INTER_LINEAR` 또는 `cv2.INTER_LANCZOS4`로 화질 저하 최소화

### 5.2 AI Super Resolution (고도화)
- 흐릿한 구형 CCTV 확대 시 픽셀 경계선 복원
- Edge GPU에서 경량 추론 가능한 Super Resolution 모델 사용

---

## 6. Medical Accreditation (인증평가) 연동

### 6.1 데이터 파이프라인
```
Vision AI Event Detection
  → Edge Server Event Log (Local DB)
  → SaaS Accreditation Module
  → 환자 안전사고 보고서 서식 자동 출력
  → 야간 보안 관찰 일지 자동 생성
```

### 6.2 출력 서식
- 환자 안전사고 보고서 (인증평가 기준 포맷)
- 야간 보안 관찰 일지
- 위험 고위험군 관찰 기록
- 외부인 출입 통제 로그

### 6.3 출력 방식
- PDF 변환 및 프린트 출력
- 한글/워드 서식 매핑 (선택 사항)

---

## 7. Business Model (SaaS)

| 구분 | 내용 | 금액 (추정) |
|------|------|------------|
| 초기 하드웨어 세팅 | Edge AI PC 1대 + 설치 | 250~300만원 (원가 100~150만원) |
| 월 구독료 | SaaS 대시보드 + AI 분석 + 인증평가 서식 | 20~40만원/월 |
| 유지보수 | HW 고장 교체, SW 업데이트 | 구독료에 포함 |

**Target:** 전국 중소 요양병원 · 요양원 · 노인전문병원

---

## 8. Development Standards

### 8.1 Tech Stack (권장)
- **Backend:** Python 3.11+, FastAPI
- **Vision:** OpenCV, ONNX Runtime (Edge 추론), YOLO-NAS/Pose 모델
- **Frontend:** React (대시보드), 실시간 WebSocket 알림
- **DB:** SQLite (초기), PostgreSQL (확장)
- **Stream:** RTSP, GStreamer 또는 FFmpeg binding
- **HW Target:** NVIDIA Jetson / RTX 30xx+ Mini PC

### 8.2 Project Structure
```
D:\medicerti-vision\
├── CLAUDE.md
├── .hermes\
│   ├── plans\
│   └── skills\
├── run.py               ← 통합 실행 스크립트 (--auto-scan, --update-check)
├── version.json          ← 버전 정보 (자동 업데이트에 사용)
├── installer\
│   ├── medicerti-vision.spec  ← PyInstaller 스펙
│   └── build.bat              ← 설치파일 빌드 스크립트
├── src\
│   ├── ingest\          ← RTSP stream reader, frame buffer
│   ├── detector\        ← Fall, Geo-fence, Face, Loitering
│   ├── privacy\         ← Silhouette masking, blur
│   ├── api\             ← FastAPI endpoints
│   ├── dashboard\       ← HTML dashboard (port 8111)
│   ├── accreditation\   ← 인증평가 서식 생성
│   ├── discovery\       ← RTSP 카메라 자동 탐지 (네트워크 스캔)
│   └── updater\         ← 자동 업데이트 시스템 (GitHub Releases)
├── tests\
├── log\
└── temp\
```

### 8.3 Coding Rules (from global_rules.md)
- **[SF] Simplicity First:** 최소 코드로 동작. RTSP 단일 파이프라인으로 시작, 멀티채널은 점진 확장
- **[PEC] Preserve Existing Code:** 병원 기존 CCTV 인프라 변경 금지. 소프트웨어만 추가
- **[TDT] Test-Driven Thinking:** 각 Detector는 Mock RTSP 입력으로 단위 테스트 필수
- **[CTC] Quality Gates:** Build → Lint → Test 순서로 통과 후에만 완료 보고
- **[REH] Robust Error Handling:** RTSP 연결 유실 시 자동 재접속 + 로그. 메모리 누수 방지
- **[PA] Performance Awareness:** Edge GPU 환경 제약 인지. 불필요한 연산 배제

### 8.4 Key Constraints
- **No cloud dependency** for video pipeline. Cloud는 대시보드 통계/설정 동기화만 허용
- **Frame drop over queue stall:** 실시간성 우선. 큐 가득 차면 구형 프레임 폐기
- **All face embeddings** must be stored encrypted, local only
- **Max model size:** Edge GPU VRAM (8~12GB) 내에서 4~8채널 병렬 추론 가능해야 함

---

## 9. Verification Gates

| Phase | Check |
|-------|-------|
| 단위 검증 | 각 Detector가 Mock RTSP에서 Fall/Loitering/Stranger 이벤트를 정확히 발생시키는가 |
| privacy 검증 | 평시 Silhouette 마스킹이 원본 식별을 차단하는가, Alarm 시 정상 해제되는가 |
| 성능 검증 | 4채널 동시 RTSP에서 프레임 드롭률 < 5%, 추론 지연 < 200ms |
| 내구성 검증 | 24시간 연속 구동 시 메모리 누수 0, RTSP 재연결 성공률 100% |
| 인증평가 검증 | 생성된 PDF 보고서가 인증평가 서식 기준을 충족하는가 |

---

## 11. Camera Auto-Discovery

### 11.1 동작 방식
- `run.py --auto-scan` 또는 API `POST /scan/cameras`
- 로컬 서브넷을 `/24` 범위로 스캔 (포트 554, 8554)
- 각 IP에 대해 20개 이상의 공통 RTSP 경로 시도
- 탐지된 카메라는 `cam_192_168_1_100` 형식으로 ID 자동 할당

### 11.2 지원 브랜드
Hikvision, Dahua, Axis, Bosch, Samsung, Hanwha — ONVIF/RTSP 표준 준수 카메라

---

## 12. Auto-Update System

### 12.1 업데이트 흐름
```
시작 시 --update-check
  → version.json 읽기 (현재 버전)
  → GitHub Releases API 조회
  → 최신 버전과 비교
  → 업데이트 있으면 다운로드 → 백업 → 파일 교체
```

### 12.2 API 엔드포인트
- `GET /update/check` — 업데이트 확인
- `POST /update/apply` — 업데이트 적용
- `GET /version` — 현재 버전 조회

### 12.3 롤백 안전장치
- 업데이트 전 `backup/YYYYMMDD_HHMMSS/` 에 자동 백업
- 업데이트 실패 시 로그만 기록, 기존 버전 유지

---

## 13. Installer Build

### 13.1 빌드 명령
```powershell
cd D:\medicerti-vision
installer\build.bat
```

### 13.2 출력
- `dist\medicerti-vision.exe` — 단일 실행파일
- `dist\run_medicerti.bat` — 실행 시 자동 스캔 + 대시보드 오픈

### 13.3 빌드 환경
- Python 3.11 + PyInstaller
- OpenCV, MediaPipe, FastAPI 등 모든 의존성을 단일 바이너리로 번들

---

## 14. Edge Cases & Risk Mitigation

| Risk | Mitigation |
|------|-----------|
| RTSP 스트림 불안정 (연결 끊김) | 자동 재접속 루프 (exponential backoff) + 연결 유실 로그 |
| 야간 IR 화질 저하 | Super Resolution 모델로 보간. Skeleton 기반이라 명암비만 유지되면 OK |
| 오탐 (False Positive) | 이벤트 발생 조건 다중 임계값 + 관리자 확인 워크플로우 |
| GPU 메모리 부족 | 모델 경량화 (INT8 양자화), 채널별 스케줄링 |
| 개인정보보호법 위반 리스크 | On-Premise + 암호화 저장 + 실루엣 마스킹 3중 안전장치 |
