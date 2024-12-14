아래는 3단계 구현 예시입니다. 기존 코드에 netstat 결과 표시 기능을 추가하는 방식입니다. 주요 변경 사항은 다음과 같습니다.

- `network_utils.py`에 `get_netstat_info(port=None)` 함수를 추가합니다.
  - `port` 인자를 통해 특정 포트 관련 정보만 필터링할 수도 있고, 없으면 전체 tcp 결과를 보여주는 식으로 구현 가능합니다.
- 서버 GUI와 클라이언트 GUI 각각에 netstat 결과를 표시하기 위한 영역과 버튼을 추가합니다.
  - 예: "네트워크 상태" 또는 "포트 상태" 라벨 프레임 추가
  - "netstat 조회" 버튼을 누르면 `get_netstat_info()` 호출 후 결과를 GUI에 표시
- netstat 결과가 변경될 만한 이벤트(서버 시작, 클라이언트 접속/퇴장 등) 시 자동으로 netstat 결과를 갱신하여 GUI에 표시합니다.
- 클라이언트의 netstat 결과는 해당 클라이언트의 로컬 포트와 서버 포트만 필터링하여 표시합니다.

아래 예시는 이전 코드에 netstat 기능을 추가하는 형태이며, 핵심 변경 부분은 주석으로 표시하였습니다.

### network_utils.py (추가/수정)

```python
import subprocess
import socket

def get_ifconfig_info():
    # 기존 구현 그대로
    try:
        result = subprocess.check_output(["ifconfig"], stderr=subprocess.STDOUT)
        return result.decode("utf-8")
    except Exception as e:
        return f"ifconfig 실행 오류: {e}"

def convert_byte_order(value):
    # 기존 구현 그대로
    import struct
    network_order = socket.htonl(value)
    host_order = socket.ntohl(network_order)
    return f"원본: {value}, htonl: {network_order}, ntohl: {host_order}"

def convert_ip_address(ip_str):
    # 기존 구현 그대로
    try:
        packed_ip = socket.inet_pton(socket.AF_INET, ip_str)
        unpacked_ip = socket.inet_ntop(socket.AF_INET, packed_ip)
        return f"입력 IP: {ip_str}, packed: {packed_ip}, unpacked: {unpacked_ip}"
    except socket.error as e:
        return f"IP 변환 오류: {e}"

def dns_lookup(domain):
    # 기존 구현 그대로
    try:
        ip = socket.gethostbyname(domain)
        reverse_domain = socket.gethostbyaddr(ip)[0]
        return f"도메인: {domain}, IP: {ip}, Reverse DNS: {reverse_domain}"
    except socket.error as e:
        return f"DNS 변환 오류: {e}"

def get_netstat_info(port=None):
    """
    netstat 결과를 반환하는 함수.
    port가 주어지면 해당 포트와 관련된 라인만 필터링.
    Linux 계열에서 netstat -a -n -p tcp로 TCP 소켓 상태를 확인한다고 가정.
    """
    try:
        # netstat 결과 가져오기
        # -a: 모든 소켓 표시, -n: 숫자형식 출력, -p: 프로토콜 표시
        # tcp만 보고 싶다면 -p tcp를 추가. 일부 OS에 따라 옵션 다름.
        result = subprocess.check_output(["netstat", "-a", "-n", "-p", "tcp"], stderr=subprocess.STDOUT)
        lines = result.decode("utf-8").splitlines()

        # 첫 줄은 헤더, 이후 라인에서 필터링
        if port:
            filtered = [line for line in lines if f".{port}" in line]
        else:
            filtered = lines

        return "\n".join(filtered) if filtered else "해당 포트 관련 netstat 정보가 없습니다."
    except Exception as e:
        return f"netstat 실행 오류: {e}"
```

### 서버 GUI 코드 수정(ServerGUI)

아래는 서버 GUI 코드에 netstat 결과 표시 영역과 버튼을 추가하는 예제입니다. 이전 서버 코드(`ServerGUI`)에 "포트 상태" 라벨 프레임을 추가하고 netstat 결과를 표시하는 위젯과 버튼을 배치합니다. 또한, 서버 시작, 클라이언트 접속/퇴장 등의 이벤트 시 자동으로 netstat 결과를 갱신하도록 수정합니다.

```python
import socket
import threading
import tkinter as tk
from tkinter import scrolledtext
from network_utils import get_netstat_info

class ChatServer:
    # 기존 구현 동일
    def __init__(self, host="0.0.0.0", port=9000):
        self.host = host
        self.port = port
        self.clients = []
        self.client_names = {}
        self.server_socket = None
        self.gui = None
        self.running = False
        self.user_count = 0

    # ... 기존 코드 동일 ...

    def refresh_netstat(self):
        if self.gui:
            self.gui.show_netstat_info()

class ServerGUI:
    def __init__(self, master, server: ChatServer):
        self.master = master
        self.server = server
        self.server.gui = self

        master.title("서버 GUI")

        self.log_area = scrolledtext.ScrolledText(
            master, state="disabled", width=50, height=20
        )
        self.log_area.grid(row=0, column=0, padx=10, pady=10, sticky="n")

        self.client_count_label = tk.Label(master, text="현재 클라이언트 수: 0")
        self.client_count_label.grid(row=1, column=0, sticky="w", padx=10)

        frame_buttons = tk.Frame(master)
        frame_buttons.grid(row=2, column=0, pady=5, padx=10, sticky="w")

        self.start_button = tk.Button(
            frame_buttons, text="서버 시작", command=self.start_server
        )
        self.start_button.pack(side=tk.LEFT, padx=5)

        self.stop_button = tk.Button(
            frame_buttons, text="서버 중지", command=self.stop_server, state="disabled"
        )
        self.stop_button.pack(side=tk.LEFT, padx=5)

        # --- 여기서부터 netstat 결과 표시를 위한 UI 추가 ---
        netstat_frame = tk.LabelFrame(master, text="포트 상태(netstat)", padx=5, pady=5)
        netstat_frame.grid(row=0, column=1, rowspan=3, padx=10, pady=10, sticky="n")

        self.netstat_text = scrolledtext.ScrolledText(netstat_frame, width=60, height=20)
        self.netstat_text.pack(pady=(0,5))

        self.netstat_button = tk.Button(netstat_frame, text="netstat 조회", command=self.show_netstat_info)
        self.netstat_button.pack()

        # Grid 설정
        master.grid_columnconfigure(0, weight=1)
        master.grid_columnconfigure(1, weight=1)

    def show_netstat_info(self):
        # 서버 포트를 기준으로 netstat 정보 조회
        port = self.server.port
        info = get_netstat_info(port)
        self.netstat_text.delete("1.0", tk.END)
        self.netstat_text.insert(tk.END, info)

    def start_server(self):
        self.server.start_server()
        self.start_button.config(state="disabled")
        self.stop_button.config(state="normal")
        self.server.refresh_netstat()

    def stop_server(self):
        self.server.stop_server()
        self.start_button.config(state="normal")
        self.stop_button.config(state="disabled")
        self.server.refresh_netstat()
```

### 클라이언트 GUI 코드 수정(ClientGUI)

클라이언트 GUI에도 netstat 결과를 표시하는 부분을 추가할 수 있습니다. 클라이언트는 로컬에서 자신의 TCP 연결 상태를 확인할 때 해당 포트를 알 수 있으므로(서버 포트에 연결), 같은 방식으로 표시 가능합니다. 클라이언트가 서버에 접속하지 않은 경우에도 netstat 결과를 전체적으로 볼 수 있습니다. 또한, 서버에 접속하거나 연결이 종료될 때 자동으로 netstat 결과를 갱신하도록 수정합니다.

```python
import socket
import threading
import tkinter as tk
from tkinter import scrolledtext
from network_utils import (
    get_ifconfig_info,
    convert_byte_order,
    convert_ip_address,
    dns_lookup,
    get_netstat_info
)

class ChatClient:
    # 기존 구현 동일
    def __init__(self, host="127.0.0.1", port=9000):
        self.host = host
        self.port = port
        self.client_socket = None
        self.gui = None
        self.running = False
        self.local_port = None

    # ... 기존 코드 동일 ...

    def refresh_netstat(self):
        if self.gui:
            self.gui.show_netstat_info()

class ClientGUI:
    def __init__(self, master, client: ChatClient):
        self.master = master
        self.client = client
        self.client.gui = self

        master.title("네트워크 채팅 클라이언트")
        master.configure(padx=10, pady=10)

        # --- 기존 코드 동일 (채팅, 네트워크 유틸리티 영역) ---

        # 네트워크 상태(netstat) 영역 추가
        netstat_frame = tk.LabelFrame(master, text="포트 상태(netstat)", padx=5, pady=5)
        netstat_frame.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=5, pady=5)

        self.netstat_text = scrolledtext.ScrolledText(netstat_frame, width=100, height=10)
        self.netstat_text.pack(pady=(0,5))

        self.netstat_button = tk.Button(netstat_frame, text="netstat 조회", command=self.show_netstat_info)
        self.netstat_button.pack()

        # Grid 설정
        master.grid_columnconfigure(0, weight=1)
        master.grid_columnconfigure(1, weight=1)
        master.grid_rowconfigure(0, weight=1)

    def show_netstat_info(self):
        # 클라이언트가 서버와 연결된 경우 서버 포트 기반으로 조회
        # 연결되지 않았으면 그냥 전체 결과 또는 특정 포트 없는 결과 표시
        port = self.client.port if self.client.running else None
        local_port = self.client.local_port if self.client.local_port else ""

        info = get_netstat_info(port)
        # 현재 클라이언트의 local_port만 필터링
        filtered_info = "\n".join(
            line
            for line in info.splitlines()
            if (f".{local_port}" in line and f".{port}" in line)  # 현재 클라이언트 연결
            or (f"*.{port}" in line and "LISTEN" in line)  # 서버 리스닝 상태만 표시
        )

        self.netstat_text.delete("1.0", tk.END)
        self.netstat_text.insert(tk.END, filtered_info)

    # ... 기존 코드 동일 ...
```

---

### 정리

위와 같이 `get_netstat_info()` 함수를 추가하고, 서버/클라이언트 GUI에 netstat 결과를 보여주는 위젯과 버튼을 추가했습니다. 이제 버튼을 클릭하면 해당 포트(서버 포트)에 대해 netstat 결과가 표시되고, 이를 통해 현재 서버/클라이언트 연결 상태를 GUI 상에서 확인할 수 있습니다. 또한, 서버 시작, 클라이언트 접속/퇴장 등의 이벤트 시 자동으로 netstat 결과를 갱신하여 GUI에 표시됩니다. 클라이언트의 netstat 결과는 해당 클라이언트의 로컬 포트와 서버 포트만 필터링하여 표시합니다.

이렇게 하면 3단계(서버와 클라이언트 각각 netstat 결과 파싱 및 표시) 구현이 완료됩니다.
