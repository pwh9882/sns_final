# 스마트네트워크서비스 기말과제

## 팀 pwh - 20203070 박우혁

<https://youtu.be/J-WCLHKIoJ8>

Python 기반 GUI 채팅 프로그램의 구현 계획입니다. 목표는 채팅 프로그램에서 사용되는 서버와 클라이언트 간 네트워크 통신 과정 및 관련 네트워크 정보를 GUI에서 실시간으로 확인할 수 있도록 하는 것입니다. 이를 위해 TCP 통신을 기반으로 설계하고, 각 단계별 네트워크 상태를 시각적으로 표현하도록 구성합니다.
아래는 "네트워크 그림판" 기능에 대해 이전보다 단순화된 요구사항을 반영한 업데이트된 구현 계획입니다. 핵심은 별도의 복잡한 다이어그램 라이브러리가 아닌, 기본 GUI 드로잉 캔버스를 통해 마우스 이벤트로 그림을 그리고, 이 정보(좌표/그림 이벤트)를 TCP로 다른 클라이언트와 동기화하는 형태로 구현하는 것입니다.

---

### **1. 요구사항 분석(업데이트 후)**

- **주요 기능**

  1. **기본 채팅 기능**: 서버-클라이언트 간 텍스트 메시지 송수신
  2. **네트워크 정보 확인**:
     - `ifconfig`로 네트워크 인터페이스 정보 확인
     - 호스트 바이트 <-> 네트워크 바이트 변환 확인
     - IP 주소 변환 (`inet_pton`, `inet_ntop`)
     - DNS 변환 (도메인 <-> IP)
  3. **서버/클라이언트 상태 시각화**:
     - `netstat` 명령어 결과를 통한 포트 상태 확인
     - TCP 서버/클라이언트 상태를 GUI로 표시
     - 송수신 버퍼 상태 확인
  4. **네트워크 그림판(간소화)**:
     - 윈도우즈 그림판과 유사한 간단한 캔버스 제공
     - 마우스 드래그로 선 그리기 가능
     - 그려진 정보(좌표, 색상, 선 두께 등)를 TCP로 동기화하여 모든 참여자가 동일한 화면을 실시간 공유

- **사용 기술**
  - **GUI 프레임워크:** Tkinter 또는 PyQt (캔버스 위젯 사용)
  - **네트워크 통신:** Python `socket` 라이브러리
  - **CLI 명령 실행:** `subprocess` 사용
  - **데이터 처리:** `socket`, `struct` 등 기본 라이브러리 사용

---

### **2. 프로그램 구조**

#### **(1) 채팅 기능**

- **서버**

  - TCP 소켓으로 클라이언트 연결 수락
  - 텍스트 메시지 송수신 처리
  - 서버 정보(IP, 포트)와 연결 상태를 GUI에 표시

- **클라이언트**
  - 서버에 TCP로 연결
  - 텍스트 메시지 송수신 처리
  - 연결 상태를 GUI에 표시

#### **(2) 네트워크 정보 확인**

- **네트워크 인터페이스 정보 (ifconfig)**
  - `subprocess`로 `ifconfig` 실행 결과 파싱 후 GUI에 표시
- **바이트 정렬 변환**
  - `htonl`, `ntohl` 등의 예제를 통해 호스트 바이트/네트워크 바이트 변환 결과를 GUI에 표시
- **IP 주소 변환**
  - `socket.inet_pton`, `socket.inet_ntop`를 통한 IP 변환 예제 표시
- **DNS 변환**
  - `socket.gethostbyname`, `socket.gethostbyaddr`를 통한 도메인/호스트명 <-> IP 변환 기능

#### **(3) 네트워크 상태 시각화**

- **명령어 기반 상태 확인 (netstat)**
  - `netstat -a -n -p tcp` 실행 결과 파싱 후 특정 포트 상태를 GUI에 표시
- **송수신 버퍼 상태**
  - 소켓의 송수신 버퍼 상태(크기, 사용량)를 주기적으로 확인하고 GUI에 업데이트

#### **(4) 네트워크 그림판 (간소화)**

- **기능 상세**
  - Tkinter Canvas 또는 PyQt의 QCanvas(또는 QPainter) 등을 활용
  - 마우스 클릭 & 드래그로 선을 그릴 수 있는 기능 구현
  - 그려진 선의 좌표, 색상, 선 두께 등을 서버를 통해 다른 클라이언트에 전달
  - 모든 클라이언트는 수신한 드로잉 명령에 따라 자신의 캔버스에 동일한 그림을 실시간으로 렌더링
  - 매우 단순한 형태(기본 선 그리기)로 제한

---

### **3. 구현 계획**

#### **(1) 기술 스택**

- **Python 라이브러리**
  - `socket`: TCP 통신 구현
  - `tkinter` 또는 `PyQt5`: GUI 및 캔버스 구현
  - `subprocess`: `ifconfig`, `netstat` 등의 CLI 명령 실행
  - `threading`: 서버/클라이언트 비동기 통신
- **주요 구조**
  - **서버**:
    - 클라이언트 연결 관리 스레드
    - 채팅 메시지 및 그림판 이벤트 브로드캐스트
  - **클라이언트**:
    - 서버와의 수신 스레드
    - 캔버스 이벤트 감지 후 서버 전송

#### **(2) GUI 설계**

- **메인 창**
  - 서버/클라이언트 시작/종료 버튼
  - 네트워크 정보 영역 (ifconfig 결과, IP 변환 결과, DNS 결과 등)
  - netstat 결과 표시 영역
- **채팅 영역**
  - 메시지 입력 박스, 전송 버튼
  - 수신 메시지 표시 박스
  - 연결 정보 표시 (현재 연결된 클라이언트 수 등)
- **네트워크 그림판 영역**
  - 단순한 캔버스 위젯
  - 마우스 드래그로 선 그리기
  - 그린 좌표 정보를 서버/클라이언트 간 송수신

#### **(3) 기능 개발 순서**

1. **기본 통신 구현**
   - 서버: 클라이언트 연결 수락, 채팅 메시지 브로드캐스트
   - 클라이언트: 서버 연결, 메시지 수신 표시
2. **네트워크 정보 추출 기능 구현**
   - `ifconfig` 결과 파싱 및 표시
   - IP/DNS 변환, 바이트 정렬 변환 기능 구현 및 GUI 표시
3. **CLI 결과 시각화**
   - `netstat` 실행 및 결과 파싱 후 GUI 업데이트
4. **네트워크 그림판 구현**
   - 캔버스 위젯 생성
   - 마우스 이벤트(버튼눌림, 드래그, 뗌) 처리
   - 서버를 통한 드로잉 정보 동기화(좌표 전송)
   - 수신한 드로잉 정보로 각 클라이언트 캔버스 업데이트
5. **GUI 통합 및 최종 테스트**
   - 모든 기능을 하나의 통합 GUI로 제공
   - 예외 상황(클라이언트 접속 해제, 오류) 처리

---

### **4. 개발 단계**

1. **단계 1:** 채팅 기능 (서버-클라이언트) 기본 구현
2. **단계 2:** 네트워크 정보 확인 (ifconfig, IP 변환, DNS 변환) 및 GUI 표시
3. **단계 3:** netstat 결과 파싱 및 표시
4. **단계 4:** 간단한 네트워크 그림판(캔버스) 기능 구현 및 통신 동기화
5. **단계 5:** 최종 통합, UI 개선, 안정성 테스트

---

### **5. 예상 결과**

- **채팅 및 네트워크 정보 확인 가능**: 텍스트 채팅, 네트워크 인터페이스 정보, IP 변환, DNS 변환, netstat 결과를 한 화면에서 확인
- **네트워크 그림판**: 마우스 드래그로 간단한 선을 그릴 수 있고, 해당 정보를 서버를 통해 다른 클라이언트에 실시간 공유
- **실시간 상태 표시**: 서버-클라이언트 간의 통신 상태, 송수신 버퍼 상태 등을 GUI에서 실시간 확인 가능

---
