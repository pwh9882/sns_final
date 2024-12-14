아래 예시는 **1단계: 채팅 기능 (서버-클라이언트) 기본 구현**에 해당하는 예시 코드입니다.  
이 단계에서는 GUI를 단순한 형태로 구현하고, 서버와 클라이언트 간 텍스트 메시지를 송수신하는 기능에 집중합니다.  
이후 단계에서 네트워크 정보 확인, 그림판 기능 등을 손쉽게 추가할 수 있도록 코드를 모듈화하고 클래스 구조를 마련해 둡니다.

아래 코드는 다음과 같은 특징을 갖습니다.

- **서버 (server.py)**

  - TCP 소켓 서버를 구동하고, 다수의 클라이언트 연결을 수락합니다.
  - 각 클라이언트로부터 수신한 메시지를 다른 모든 클라이언트에게 브로드캐스트합니다.
  - 향후 그림판 정보나 네트워크 상태 정보를 같은 방식으로 브로드캐스트할 수 있습니다.
  - GUI를 통해 현재 접속한 클라이언트 수, 서버 상태 등을 확인할 수 있도록 기본 구조를 마련합니다.

- **클라이언트 (client.py)**

  - 서버에 TCP로 연결 후, 메시지를 송신하고 수신하는 기능을 구현합니다.
  - Tkinter 기반 간단한 대화창을 제공하며, 이후 네트워크 정보 표시 및 그림판 캔버스를 추가하기 용이하도록 레이아웃을 단순화했습니다.

- **인수인계 사항(향후 확장 가이드)**

  1. **네트워크 정보 출력 기능 추가**:

     - `subprocess` 모듈을 사용한 `ifconfig`, `netstat` 결과 파싱 로직을 추가하는 함수를 별도 모듈로 작성하고, GUI 업데이트 부분을 해당 함수 호출 시 반영.
     - IP 변환, DNS 변환 함수를 별도로 유틸리티 모듈(`network_utils.py`)로 관리하고, GUI에 표현하는 Label이나 Text 위젯 추가 가능.

  2. **네트워크 그림판 기능 추가**:

     - Tkinter Canvas 위젯 추가 후, 마우스 이벤트(버튼 클릭/드래그) 바인딩.
     - 그림판 이벤트 발생 시 서버로 좌표/색상/두께 정보를 송신하는 함수를 구현(`send_draw_event`)하고, 수신한 이벤트를 해석하여 Canvas에 동일하게 반영.
     - 현재 채팅 메시지를 브로드캐스트 하는 부분과 유사한 형태로 그림 이벤트도 브로드캐스트.

  3. **클래스 구조 개선**:
     - 현재는 단일 파일에 클래스 혹은 함수를 모아 두었으나, 추후 `Server`, `Client`, `GUIManager`, `NetworkUtil` 등의 클래스로 세분화하여 유지보수를 용이하게 할 수 있음.
     - 서버와 클라이언트 측 모두 메시지 처리/그림판 이벤트 처리 로직을 핸들러로 분리하여 가독성 향상.

---

## 예시 코드

### server.py (서버 코드 예시)

```python
import socket
import threading
import tkinter as tk
from tkinter import scrolledtext

class ChatServer:
    def __init__(self, host='0.0.0.0', port=5000):
        self.host = host
        self.port = port
        self.clients = []
        self.server_socket = None
        self.gui = None
        self.running = False

    def start_server(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen()
        self.running = True
        self.log_message(f"서버 시작: {self.host}:{self.port}")

        threading.Thread(target=self.accept_clients, daemon=True).start()

    def accept_clients(self):
        while self.running:
            client_socket, addr = self.server_socket.accept()
            self.clients.append(client_socket)
            self.log_message(f"클라이언트 접속: {addr}")
            threading.Thread(target=self.handle_client, args=(client_socket,), daemon=True).start()
            self.update_client_count()

    def handle_client(self, client_socket):
        while self.running:
            try:
                data = client_socket.recv(1024)
                if not data:
                    break
                message = data.decode('utf-8')
                self.broadcast_message(message, exclude=client_socket)
                self.log_message(f"[클라이언트] {message}")
            except:
                break
        self.remove_client(client_socket)

    def broadcast_message(self, message, exclude=None):
        for c in self.clients:
            if c != exclude:
                try:
                    c.sendall(message.encode('utf-8'))
                except:
                    self.remove_client(c)

    def remove_client(self, client_socket):
        if client_socket in self.clients:
            self.clients.remove(client_socket)
            client_socket.close()
            self.log_message("클라이언트 종료")
            self.update_client_count()

    def stop_server(self):
        self.running = False
        for c in self.clients:
            c.close()
        self.server_socket.close()
        self.log_message("서버 중지")

    def update_client_count(self):
        if self.gui:
            self.gui.client_count_label.config(text=f"현재 클라이언트 수: {len(self.clients)}")

    def log_message(self, msg):
        if self.gui:
            self.gui.log_area.config(state='normal')
            self.gui.log_area.insert(tk.END, msg + '\n')
            self.gui.log_area.see(tk.END)
            self.gui.log_area.config(state='disabled')
        print(msg)

class ServerGUI:
    def __init__(self, master, server: ChatServer):
        self.master = master
        self.server = server
        self.server.gui = self

        master.title("서버 GUI")

        # 로그 출력 영역
        self.log_area = scrolledtext.ScrolledText(master, state='disabled', width=50, height=20)
        self.log_area.grid(row=0, column=0, padx=10, pady=10)

        # 클라이언트 수 표시 레이블
        self.client_count_label = tk.Label(master, text="현재 클라이언트 수: 0")
        self.client_count_label.grid(row=1, column=0, sticky='w', padx=10)

        # 서버 제어 버튼
        self.start_button = tk.Button(master, text="서버 시작", command=self.start_server)
        self.start_button.grid(row=2, column=0, sticky='w', padx=10, pady=5)
        self.stop_button = tk.Button(master, text="서버 중지", command=self.stop_server)
        self.stop_button.grid(row=2, column=0, sticky='e', padx=10, pady=5)

    def start_server(self):
        self.server.start_server()

    def stop_server(self):
        self.server.stop_server()

if __name__ == "__main__":
    root = tk.Tk()
    server = ChatServer(host='0.0.0.0', port=5000)
    gui = ServerGUI(root, server)
    root.mainloop()
```

---

### client.py (클라이언트 코드 예시)

```python
import socket
import threading
import tkinter as tk
from tkinter import scrolledtext

class ChatClient:
    def __init__(self, host='127.0.0.1', port=5000):
        self.host = host
        self.port = port
        self.client_socket = None
        self.gui = None
        self.running = False

    def connect_to_server(self):
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.client_socket.connect((self.host, self.port))
            self.running = True
            self.log_message("서버에 연결되었습니다.")
            threading.Thread(target=self.receive_messages, daemon=True).start()
        except Exception as e:
            self.log_message(f"서버 접속 실패: {e}")

    def receive_messages(self):
        while self.running:
            try:
                data = self.client_socket.recv(1024)
                if not data:
                    break
                message = data.decode('utf-8')
                self.append_message(message)
            except:
                break
        self.log_message("서버와의 연결이 종료되었습니다.")
        self.running = False

    def send_message(self, message):
        if self.running and message.strip():
            self.client_socket.sendall(message.encode('utf-8'))
            self.append_message(f"(나) {message}")

    def append_message(self, msg):
        if self.gui:
            self.gui.chat_area.config(state='normal')
            self.gui.chat_area.insert(tk.END, msg + '\n')
            self.gui.chat_area.see(tk.END)
            self.gui.chat_area.config(state='disabled')
        print(msg)

    def log_message(self, msg):
        # 로그나 상태 메세지는 별도로 표시할 수 있으나 여기서는 콘솔로 출력
        # 추후 GUI에 상태 표시용 Label 추가 가능
        print(msg)

    def disconnect(self):
        self.running = False
        if self.client_socket:
            self.client_socket.close()

class ClientGUI:
    def __init__(self, master, client: ChatClient):
        self.master = master
        self.client = client
        self.client.gui = self

        master.title("클라이언트 GUI")

        # 채팅 메시지 출력 영역
        self.chat_area = scrolledtext.ScrolledText(master, state='disabled', width=50, height=20)
        self.chat_area.grid(row=0, column=0, padx=10, pady=10)

        # 메시지 입력
        self.entry_message = tk.Entry(master, width=40)
        self.entry_message.grid(row=1, column=0, padx=10, sticky='w')
        self.send_button = tk.Button(master, text="전송", command=self.send_message)
        self.send_button.grid(row=1, column=0, sticky='e', padx=10)

        # 서버 접속/해제 버튼
        self.connect_button = tk.Button(master, text="서버 접속", command=self.connect_server)
        self.connect_button.grid(row=2, column=0, sticky='w', padx=10, pady=5)
        self.disconnect_button = tk.Button(master, text="접속 해제", command=self.disconnect_server)
        self.disconnect_button.grid(row=2, column=0, sticky='e', padx=10, pady=5)

    def connect_server(self):
        host = self.client.host
        port = self.client.port
        self.client.connect_to_server()

    def disconnect_server(self):
        self.client.disconnect()

    def send_message(self):
        message = self.entry_message.get()
        self.client.send_message(message)
        self.entry_message.delete(0, tk.END)

if __name__ == "__main__":
    root = tk.Tk()
    client = ChatClient(host='127.0.0.1', port=5000)
    gui = ClientGUI(root, client)
    root.mainloop()
```

---

## 인수인계 및 향후 확장 방법

1. **서버/클라이언트 구조 이해**:

   - `ChatServer`와 `ChatClient` 클래스는 각각 서버와 클라이언트의 핵심 로직(소켓 통신, 메시지 송수신 관리)을 담당합니다.
   - GUI 클래스(`ServerGUI`, `ClientGUI`)는 Tkinter 위젯을 사용해 시각적 인터페이스를 제공하며, 서버/클라이언트 객체를 받아서 동작합니다.

2. **네트워크 정보 및 그림판 추가 방안**:

   - 네트워크 정보(예: ifconfig 결과, netstat 결과)를 확인하기 위한 코드를 추가할 경우, `ChatServer`나 `ChatClient` 클래스에 직접 넣기보다는 별도의 모듈(예: `network_utils.py`)에 함수로 구현하고, GUI에서 해당 함수의 결과를 호출해 출력하는 방식으로 구조화할 수 있습니다.
   - 그림판 기능을 추가할 때는 `ClientGUI`와 `ServerGUI`에 Canvas 위젯을 추가하고, 마우스 이벤트를 바인딩하여 그림 좌표 데이터를 수집한 후, `ChatClient`(클라이언트) → `ChatServer`(서버) → 다른 클라이언트들로 브로드캐스트하는 흐름을 유지하면 됩니다.

3. **스레드 및 예외 처리**:

   - 현재 구현은 기본적인 예외 처리만 되어 있습니다. 향후 클라이언트가 비정상 종료하는 경우나 서버 정지 시 예외 처리 로직을 보강할 수 있습니다.
   - 스레드 동기화 이슈(예: GUI 업데이트를 메인 스레드에서만 처리하도록 `queue`나 `after` 메서드 사용) 등을 고려해 안정성을 개선할 수 있습니다.

4. **코드 모듈화**:
   - 현재 단계에서는 하나의 Python 파일(서버용, 클라이언트용)로 작성했지만, 점차 모듈을 나누어 유지보수를 용이하게 하는 것이 좋습니다.
   - 예:
     - `server.py`, `client.py` : 메인 실행 스크립트
     - `gui.py`: 공통 GUI 기능 또는 GUI 클래스 분리
     - `network_utils.py`: DNS 변환, IP 변환, ifconfig 등 네트워크 유틸리티 함수
     - `drawing.py`: 그림판 관련 기능 모듈화

이러한 인수인계 사항을 바탕으로 이후 단계(네트워크 정보 확인, 그림판 기능 추가, UI 개선)에 용이하게 확장할 수 있습니다.
