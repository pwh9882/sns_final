# Python GUI 네트워크 프로그래밍 발표

## 슬라이드 1: 프로젝트 개요

- 프로젝트명: Python GUI 네트워크 프로그래밍
- 구현 기능: 채팅, 네트워크 정보 확인, 공유 그림판
- 개발 언어: Python 3
- 사용 라이브러리: Tkinter, socket, threading, json

## 슬라이드 2: 주요 구현 사항

1. TCP 소켓 기반 채팅 서버/클라이언트
2. 네트워크 정보 확인 유틸리티
3. 실시간 netstat 정보 표시
4. 공유 그림판 기능

## 슬라이드 3: 시스템 아키텍처

### 서버

- TCP 소켓 서버 (멀티 클라이언트 지원)
- GUI 기반 서버 관리 인터페이스
- 클라이언트 접속 관리 및 이벤트 브로드캐스팅

### 클라이언트

- TCP 소켓 클라이언트
- 통합 GUI 인터페이스 (채팅, 네트워크 정보, 그림판)
- 비동기 메시지 처리

## 슬라이드 4: GUI 레이아웃

1. 채팅 영역

   - 메시지 표시 창
   - 입력 창 및 전송 버튼
   - 서버 연결/해제 버튼

2. 네트워크 유틸리티 영역

   - ifconfig 정보 표시
   - 바이트 순서 변환
   - IP 주소 변환
   - DNS 조회

3. 그림판 영역
   - 드로잉 캔버스
   - Clear 버튼
   - 디버그 로그 창

## 슬라이드 5: 핵심 기능 구현

### 채팅 시스템

```python
# 메시지 송수신 예시
def send_message(self, message):
    if self.running and message.strip():
        full_message = message + "\n"
        self.client_socket.sendall(full_message.encode("utf-8"))
```

### 네트워크 정보 표시

```python
# 바이트 순서 변환 예시
def convert_byte_order(value):
    network_order = socket.htonl(value)
    host_order = socket.ntohl(network_order)
    return f"원본: {value} (0x{value:08x})\n..."
```

## 슬라이드 6: 그림판 구현

```python
# 그리기 이벤트 처리
def draw(self, event):
    if self.drawing:
        self.canvas.create_line(
            self.local_last_x,
            self.local_last_y,
            event.x,
            event.y,
            fill="black",
            width=2,
        )
```

## 슬라이드 7: 주요 개선사항

1. 서버 포트 재사용 문제 해결

   - SO_REUSEADDR 옵션 설정
   - 소켓 완전 종료 대기 추가

2. GUI 사용성 개선

   - Enter 키로 메시지 전송
   - 읽기 전용 텍스트 박스 구현

3. 그림판 기능 개선

   - 연속적인 선 그리기 구현
   - 실시간 동기화 성능 향상

## 슬라이드 8: 시연

1. 서버 실행 및 클라이언트 연결
2. 채팅 기능 시연
3. 네트워크 정보 확인 기능 시연
4. 그림판 기능 시연
