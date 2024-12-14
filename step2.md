아래는 2단계(네트워크 정보 확인 기능) 구현 예시 및 해당 기능을 GUI에 통합하는 과정, 그리고 향후 3단계를 인수인계할 수 있도록 모듈화/구조화한 예제 코드와 설명입니다. 전반적인 목표는 기존의 ChatServer, ChatClient, ClientGUI 등의 구조에 "네트워크 정보 확인" 기능을 추가하고, 이를 GUI 상에서 표시할 수 있도록 하는 것입니다.

**고려한 요소**:

1. **모듈화**: 네트워크 정보를 가져오는 기능(예: ifconfig 결과 파싱, IP 변환, DNS 변환)은 `network_utils.py` 등 별도 파일로 분리합니다. 이렇게 하면 ChatServer나 ChatClient 클래스 내부 로직과 독립적으로 관리할 수 있고, 향후 3단계(netstat 결과 처리나 그림판 기능 추가) 시에도 쉽게 재사용하거나 확장할 수 있습니다.

2. **비동기 처리**: GUI의 `ifconfig` 실행이나 DNS 조회 등 시간이 오래 걸릴 수 있는 작업은 GUI가 멈추지 않도록 별도의 스레드나 `after` 메서드를 활용할 수 있습니다. 여기서는 간단히 메인 스레드에서 실행되더라도 큰 문제 없는 정도의 처리로 가정합니다. 만약 실행 시 지연이 발생한다면 스레드를 사용하도록 수정할 수 있습니다.

3. **GUI 업데이트**: Tkinter에서는 메인 스레드에서 위젯 업데이트를 수행하는 것이 원칙입니다. 따라서 결과를 가져온 뒤, 메인 GUI 스레드에서 Text 위젯이나 Label 등에 표시하는 방식을 사용합니다. 만약 별도 스레드로 처리 시 Queue를 사용하거나 `after`를 통해 UI 갱신을 해야 합니다.

4. **코드 구조**:
   - `network_utils.py`: ifconfig 결과 가져오기, IP 변환, DNS 변환 함수를 제공
   - `client_gui.py` (또는 통합 GUI 코드): 이 함수를 호출해 결과를 Text 위젯이나 Label에 표시
   - 이러한 구조를 통해 3단계로 넘어갈 때(netstat 결과 파싱, 그림판 등) `network_utils.py`에 새로운 함수나 다른 모듈을 추가해 계속 확장할 수 있습니다.

---

### 예시 코드

#### network_utils.py

```python
import subprocess
import socket

def get_ifconfig_info():
    """
    ifconfig 명령어 실행 결과를 문자열로 반환하는 함수.
    Unix 계열에서 동작한다고 가정 (Windows라면 ipconfig로 변경 필요)
    """
    try:
        result = subprocess.check_output(["ifconfig"], stderr=subprocess.STDOUT)
        return result.decode("utf-8")
    except Exception as e:
        return f"ifconfig 실행 오류: {e}"

def convert_byte_order(value):
    """
    호스트 바이트 순서 -> 네트워크 바이트 순서 (htonl), 다시 ntohl로 변환해 예시를 보여줌
    value는 정수형으로 가정.
    """
    import struct
    network_order = socket.htonl(value)
    host_order = socket.ntohl(network_order)
    return f"원본: {value}, htonl: {network_order}, ntohl: {host_order}"

def convert_ip_address(ip_str):
    """
    IP 문자열을 바이너리로 변환(inet_pton), 다시 문자열(inet_ntop)로 변환
    IPv4 기준 예제
    """
    try:
        packed_ip = socket.inet_pton(socket.AF_INET, ip_str)
        unpacked_ip = socket.inet_ntop(socket.AF_INET, packed_ip)
        return f"입력 IP: {ip_str}, packed: {packed_ip}, unpacked: {unpacked_ip}"
    except socket.error as e:
        return f"IP 변환 오류: {e}"

def dns_lookup(domain):
    """
    도메인을 IP로 변환, IP를 도메인으로 다시 역변환하는 예제
    """
    try:
        ip = socket.gethostbyname(domain)
        reverse_domain = socket.gethostbyaddr(ip)[0]
        return f"도메인: {domain}, IP: {ip}, Reverse DNS: {reverse_domain}"
    except socket.error as e:
        return f"DNS 변환 오류: {e}"
```

이렇게 구현하면 네트워크 정보 관련 기능을 다른 부분과 분리할 수 있습니다.

---

#### client_gui.py (ClientGUI 클래스 일부 수정)

```python
import tkinter as tk
from tkinter import scrolledtext
from network_utils import get_ifconfig_info, convert_byte_order, convert_ip_address, dns_lookup

class ClientGUI:
    def __init__(self, master, client):
        self.master = master
        self.client = client
        master.title("Chat Client")

        # 기존 채팅 GUI 영역
        self.chat_frame = tk.Frame(master)
        self.chat_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # 메시지 표시 영역
        self.text_area = scrolledtext.ScrolledText(self.chat_frame, wrap=tk.WORD, width=50, height=20)
        self.text_area.pack(pady=5)

        # 메시지 입력 & 전송
        self.entry = tk.Entry(self.chat_frame)
        self.entry.pack(side=tk.LEFT, padx=5, pady=5, fill=tk.X, expand=True)
        self.send_button = tk.Button(self.chat_frame, text="전송", command=self.send_message)
        self.send_button.pack(side=tk.LEFT, padx=5, pady=5)

        # 연결 상태 버튼
        self.connect_button = tk.Button(self.chat_frame, text="서버 연결", command=self.connect_server)
        self.connect_button.pack(pady=5)
        self.disconnect_button = tk.Button(self.chat_frame, text="연결 끊기", command=self.disconnect_server, state="disabled")
        self.disconnect_button.pack(pady=5)

        # 네트워크 정보 확인 영역
        self.info_frame = tk.Frame(master, bd=2, relief=tk.SUNKEN)
        self.info_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        tk.Label(self.info_frame, text="네트워크 정보 확인").pack(pady=5)

        # ifconfig 결과 표시
        self.ifconfig_button = tk.Button(self.info_frame, text="ifconfig 실행", command=self.show_ifconfig_info)
        self.ifconfig_button.pack(pady=5)

        self.ifconfig_text = scrolledtext.ScrolledText(self.info_frame, wrap=tk.WORD, width=50, height=10)
        self.ifconfig_text.pack(pady=5)

        # 바이트 순서 변환 예제
        self.byte_order_label = tk.Label(self.info_frame, text="바이트 순서 변환 예: 값 1234")
        self.byte_order_label.pack(pady=5)

        self.byte_order_button = tk.Button(self.info_frame, text="변환 실행", command=self.show_byte_order_conversion)
        self.byte_order_button.pack(pady=5)

        self.byte_order_result = tk.Label(self.info_frame, text="")
        self.byte_order_result.pack(pady=5)

        # IP 변환 예제
        tk.Label(self.info_frame, text="IP 변환 예: 8.8.8.8").pack(pady=5)
        self.ip_result_label = tk.Label(self.info_frame, text="")
        self.ip_result_label.pack(pady=5)
        self.ip_button = tk.Button(self.info_frame, text="IP 변환", command=self.show_ip_conversion)
        self.ip_button.pack(pady=5)

        # DNS 변환 예제
        tk.Label(self.info_frame, text="DNS 변환 예: www.google.com").pack(pady=5)
        self.dns_result_label = tk.Label(self.info_frame, text="")
        self.dns_result_label.pack(pady=5)
        self.dns_button = tk.Button(self.info_frame, text="DNS 변환", command=self.show_dns_conversion)
        self.dns_button.pack(pady=5)

    def send_message(self):
        msg = self.entry.get()
        if msg:
            self.client.send_message(msg)
            self.entry.delete(0, tk.END)

    def connect_server(self):
        self.client.connect_to_server()
        if self.client.running:
            self.update_connection_buttons(True)

    def disconnect_server(self):
        self.client.disconnect()
        self.update_connection_buttons(False)

    def update_connection_buttons(self, is_connected):
        if is_connected:
            self.connect_button.config(state="disabled")
            self.disconnect_button.config(state="normal")
        else:
            self.connect_button.config(state="normal")
            self.disconnect_button.config(state="disabled")

    def append_message(self, message):
        self.text_area.insert(tk.END, message + "\n")
        self.text_area.see(tk.END)

    # 네트워크 정보 관련 메서드
    def show_ifconfig_info(self):
        info = get_ifconfig_info()
        self.ifconfig_text.delete("1.0", tk.END)
        self.ifconfig_text.insert(tk.END, info)

    def show_byte_order_conversion(self):
        result = convert_byte_order(1234)
        self.byte_order_result.config(text=result)

    def show_ip_conversion(self):
        result = convert_ip_address("8.8.8.8")
        self.ip_result_label.config(text=result)

    def show_dns_conversion(self):
        result = dns_lookup("www.google.com")
        self.dns_result_label.config(text=result)

    def log_message(self, message):
        self.append_message(message)
```

위 코드에서는 기존 `ClientGUI`에 네트워크 정보 표시 영역을 확장하였습니다. `network_utils.py` 모듈의 함수를 호출하여 결과를 `Text` 또는 `Label` 위젯에 표시합니다.

---

### 인수인계 시 고려 사항

- `network_utils.py` 모듈은 확장하기 쉽도록 독립적으로 구현되었습니다. 향후 3단계(netstat 결과 표시)에서는 `get_netstat_info()` 함수를 추가한 뒤, GUI에서 해당 함수를 호출해 결과를 표시하는 식으로 쉽게 확장할 수 있습니다.
- DNS 변환, IP 변환, 바이트 순서 변환 등은 데모용 예제이며, 필요시 인수를 받아 다양한 IP나 도메인으로 변환 가능하도록 GUI를 개선할 수 있습니다.
- 현재는 GUI Thread 내에서 ifconfig나 DNS 변환 등을 실행하는데, 필요하다면 `threading.Thread`를 사용하여 비동기적으로 실행하고, `queue`나 `after` 메서드를 통해 메인 스레드에서 UI를 업데이트하도록 개선할 수 있습니다.
- 향후 그림판 기능 추가 시에도 `drawing.py` 모듈을 두어 캔버스 관련 이벤트 처리 로직을 모듈화하고, `ClientGUI`에서는 해당 기능을 호출하는 식으로 구조화할 수 있습니다.

이러한 구현과 구조화는 3단계에 인수인계를 할 때, 코드 이해도와 확장 용이성을 높여줍니다.
