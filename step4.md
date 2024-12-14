# 4단계: 네트워크 그림판 구현

## 목표

- 서버에 하나의 공유된 캔버스를 구현
- 모든 클라이언트가 동일한 캔버스를 실시간으로 공유
- 간단한 선 그리기 기능과 초기화 기능 구현

### 구현 계획

#### 1. 메시지 프로토콜 설계

```python
# 드로잉 이벤트 메시지 형식
{
    "type": "draw",
    "action": "start"|"move"|"end",
    "x": float,
    "y": float
}

# 초기화 메시지 형식
{
    "type": "clear"
}
```

#### 2. 서버 측 구현 사항

- `ChatServer` 클래스에 캔버스 관련 기능 추가
  - 현재까지 그려진 모든 선 데이터를 저장할 리스트 구조 추가
  - 새로운 클라이언트 접속 시 현재 캔버스 상태 전송
  - 드로잉 이벤트 수신 시 모든 클라이언트에 브로드캐스트

```python
class ChatServer:
    def __init__(self):
        # ...existing code...
        self.canvas_data = []  # 그리기 데이터 저장

    def handle_client(self, client_socket):
        # 기존 채팅 처리에 드로잉 이벤트 처리 추가
        # 새 클라이언트에게 현재까지의 그리기 데이터 전송
        if self.drawing_events:
            try:
                for event in self.drawing_events:
                    client_socket.sendall(json.dumps(event).encode("utf-8"))
            except:
                pass
```

#### 3. 클라이언트 측 구현 사항

- `ClientGUI`에 캔버스 영역 추가
  - Tkinter Canvas 위젯 사용
  - 마우스 이벤트 바인딩 (Button-1, B1-Motion, ButtonRelease-1)
  - Clear 버튼 추가
  - 수신한 드로잉 이벤트를 캔버스에 반영

```python
class ClientGUI:
    def __init__(self):
        # ...existing code...
        self.setup_canvas()

    def setup_canvas(self):
        # 캔버스 프레임 생성
        canvas_frame = tk.LabelFrame(self.master, text="공유 캔버스")
        self.canvas = tk.Canvas(canvas_frame, width=400, height=300, bg="white")
        self.canvas.pack()

        # 이벤트 바인딩
        self.canvas.bind("<Button-1>", self.start_draw)
        self.canvas.bind("<B1-Motion>", self.draw)
        self.canvas.bind("<ButtonRelease-1>", self.stop_draw)

    def handle_draw_event(self, event_data):
        if event_data["action"] == "start":
            self.client.last_x = event_data["x"]
            self.client.last_y = event_data["y"]
        elif event_data["action"] == "move" and self.client.last_x is not None:
            self.canvas.create_line(
                self.client.last_x,
                self.client.last_y,
                event_data["x"],
                event_data["y"],
                width=2,
            )
            self.client.last_x = event_data["x"]
            self.client.last_y = event_data["y"]
        elif event_data["action"] == "end":
            self.client.last_x = None
            self.client.last_y = None

    def handle_clear_event(self):
        self.canvas.delete("all")
```

#### 4. 동작 흐름

1. 마우스 클릭 시작

   - `start_draw` 이벤트 발생
   - 현재 좌표 저장
   - 서버에 시작 메시지 전송

2. 마우스 드래그

   - `draw` 이벤트 발생
   - 이전 좌표에서 현재 좌표까지 선 그리기
   - 서버에 이동 메시지 전송

3. 마우스 클릭 해제

   - `stop_draw` 이벤트 발생
   - 서버에 종료 메시지 전송

4. Clear 버튼 클릭
   - 캔버스 초기화
   - 서버에 초기화 메시지 전송

#### 5. 구현 순서

1. 서버와 클라이언트에 기본 캔버스 UI 추가
2. 로컬 드로잉 기능 구현 (마우스 이벤트 처리)
3. 드로잉 이벤트의 네트워크 전송 구현
4. 수신한 드로잉 이벤트 처리 및 캔버스 업데이트
5. Clear 기능 구현
6. 새 클라이언트 접속 시 캔버스 동기화 처리

### 제약 사항

- 단순한 선 그리기만 지원 (색상, 두께 변경 없음)
- 실시간 동기화에 초점을 맞춤
- Undo/Redo 기능 없음
- 저장 기능 없음
