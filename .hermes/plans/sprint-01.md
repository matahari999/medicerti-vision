# Sprint-01: Core Pipeline MVP

**목표:** RTSP 영상 수집 → Skeleton 추정 → 낙상 감지 → 이벤트 로깅 → WebSocket 알림 PoC

## 단계

### Phase 1: Ingestion Pipeline
- [x] `src/ingest/rtsp_reader.py` — 멀티스레드 RTSP reader (frame drop queue, auto-reconnect)
- verify: 단일 RTSP 스트림에서 30fps 정상 수집 확인

### Phase 2: Pose Estimation Engine
- [ ] `src/detector/pose_estimator.py` — MediaPipe Pose 33개 랜드마크 추출
- [ ] `src/detector/fall_detector.py` — 관절 좌표 기반 낙상 패턴 감지 (급격한 수평 붕괴, 속도 벡터)
- [ ] `src/detector/geo_fence.py` — 가상 폴리곤 경계선 이탈 감지
- verify: Mock 프레임에서 Fall/Elopement 이벤트 정상 발생

### Phase 3: Privacy Masking
- [ ] `src/privacy/masker.py` — Skeleton line + Silhouette 렌더링, 평시 마스킹/알람 시 해제
- verify: 원본 영상 식별 불가능한 마스킹 확인

### Phase 4: Backend API
- [ ] `src/api/event_logger.py` — SQLite 기반 이벤트 영구 저장
- [ ] `src/api/models.py` — Pydantic 이벤트 스키마
- [ ] `src/api/main.py` — FastAPI + WebSocket 실시간 알림
- verify: `curl`로 이벤트 조회 API 정상 응답

### Phase 5: Dashboard (선택)
- [ ] `src/dashboard/` — React or HTML 대시보드 (실시간 알림 리스트)
- verify: WebSocket 연결 → Fall 이벤트 수신 확인

### Phase 6: Accreditation Module (기초)
- [ ] `src/accreditation/report_gen.py` — PDF 보고서 기본 포맷 생성
- verify: 빈 PDF 생성 확인

## Edge Cases
- RTSP 연결 유실 시 자동 재접속 (exponential backoff, max 5회)
- GPU 메모리 부족 시 채널 드롭
- 오탐 방지: 연속 3프레임 이상 Fall 조건 충족 시에만 이벤트 발생
- 프레임 드롭: 큐 maxsize=3, 오래된 프레임 자동 폐기

## Risk
- MediaPipe GPU 미지원 시 CPU 부하 → fallback to OpenCV DNN
- 실제 RTSP URL 없이 개발 → Mock 비디오 파일 모드 지원
