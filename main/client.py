import socket
import threading
import tkinter as tk
import json
from tkinter import scrolledtext
from network_utils import (
    get_ifconfig_info,
    convert_byte_order,
    convert_ip_address,
    dns_lookup,
    get_netstat_info,
)


class ChatClient:
    def __init__(self, host="127.0.0.1", port=9000):
        self.host = host
        self.port = port
        self.client_socket = None
        self.gui = None
        self.running = False
        self.local_port = None

    def connect_to_server(self):
        if not self.running:
            try:
                self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.client_socket.connect((self.host, self.port))
                self.local_port = self.client_socket.getsockname()[1]
                self.running = True
                self.log_message("서버에 연결되었습니다.")
                threading.Thread(target=self.receive_messages, daemon=True).start()
                self.refresh_netstat()
                return True
            except Exception as e:
                self.log_message(f"서버 접속 실패: {e}")
                if self.client_socket:
                    self.client_socket.close()
                self.client_socket = None
                return False

    def receive_messages(self):
        buffer = ""
        while self.running:
            try:
                data = self.client_socket.recv(1024)
                if not data:
                    break
                buffer += data.decode("utf-8")
                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    if not line.strip():
                        continue
                    try:
                        message_dict = json.loads(line)
                        if isinstance(message_dict, dict) and "type" in message_dict:
                            if message_dict["type"] == "draw":
                                self.gui.master.after(
                                    0, self.gui.handle_draw_event, message_dict
                                )
                                continue
                            elif message_dict["type"] == "clear":
                                self.gui.master.after(0, self.gui.handle_clear_event)
                                continue
                    except json.JSONDecodeError:
                        pass
                    # 일반 채팅 메시지 처리
                    self.gui.master.after(0, self.append_message, line)
            except Exception as e:
                self.log_debug(f"예외 발생: {e}")
                break
        self.log_message("서버와의 연결이 종료되었습니다.")
        self.running = False
        # GUI 버튼 상태 업데이트
        if self.gui:
            self.gui.update_connection_buttons(False)
        self.refresh_netstat()

    def send_message(self, message):
        if self.running and message.strip():
            try:
                full_message = message + "\n"  # 메시지 구분을 위한 개행 추가
                self.client_socket.sendall(full_message.encode("utf-8"))
                self.append_message(f"나: {message}")  # 자신의 메시지를 GUI에 추가
                return True
            except:
                self.log_message("메시지 전송 실패")
                self.disconnect()
                return False

    def send_draw_event(self, event_type, x, y):
        if self.running:
            try:
                draw_data = {"type": "draw", "action": event_type, "x": x, "y": y}
                full_message = (
                    json.dumps(draw_data) + "\n"
                )  # 메시지 구분을 위한 개행 추가
                self.client_socket.sendall(full_message.encode("utf-8"))
                return True
            except:
                self.log_message("드로잉 이벤트 전송 실패")
                return False

    def send_clear_event(self):
        if self.running:
            try:
                clear_data = {"type": "clear"}
                full_message = (
                    json.dumps(clear_data) + "\n"
                )  # 메시지 구분을 위한 개행 추가
                self.client_socket.sendall(full_message.encode("utf-8"))
                return True
            except:
                self.log_message("초기화 이벤트 전송 실패")
                return False

    def append_message(self, msg):
        if self.gui:
            self.gui.chat_area.config(state="normal")
            self.gui.chat_area.insert(tk.END, msg + "\n")
            self.gui.chat_area.see(tk.END)
            self.gui.chat_area.config(state="disabled")
        print(msg)

    def log_message(self, msg):
        if self.gui:
            self.gui.status_label.config(text=msg)
        print(msg)

    def disconnect(self):
        self.running = False
        if self.client_socket:
            try:
                self.client_socket.shutdown(socket.SHUT_RDWR)
                self.client_socket.close()
            except:
                pass
        self.client_socket = None
        self.log_message("서버와의 연결이 해제되었습니다.")
        self.refresh_netstat()

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

        # 채팅 영역
        chat_frame = tk.LabelFrame(master, text="채팅", padx=5, pady=5)
        chat_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

        self.chat_area = scrolledtext.ScrolledText(
            chat_frame, state="disabled", width=50, height=20
        )
        self.chat_area.pack(fill=tk.BOTH, expand=True)

        # 메시지 입력 및 전송
        input_frame = tk.Frame(chat_frame)
        input_frame.pack(fill=tk.X, pady=(5, 0))

        self.entry_message = tk.Entry(input_frame)
        self.entry_message.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.entry_message.bind("<Return>", self.send_message)  # Enter 키 이벤트 바인딩

        self.send_button = tk.Button(
            input_frame, text="전송", command=self.send_message
        )
        self.send_button.pack(side=tk.RIGHT, padx=(5, 0))

        # 연결 제어 버튼
        control_frame = tk.Frame(chat_frame)
        control_frame.pack(fill=tk.X, pady=5)

        self.connect_button = tk.Button(
            control_frame, text="서버 접속", command=self.connect_server
        )
        self.connect_button.pack(side=tk.LEFT, padx=5)

        self.disconnect_button = tk.Button(
            control_frame,
            text="접속 해제",
            command=self.disconnect_server,
            state="disabled",
        )
        self.disconnect_button.pack(side=tk.LEFT, padx=5)

        self.status_label = tk.Label(control_frame, text="서버에 연결되지 않음")
        self.status_label.pack(side=tk.RIGHT, padx=5)

        # 네트워크 유틸리티 영역
        utils_frame = tk.LabelFrame(master, text="네트워크 유틸리티", padx=5, pady=5)
        utils_frame.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)

        # 시스템 네트워크 정보
        tk.Label(utils_frame, text="시스템 네트워크 정보").pack(pady=(0, 5))
        self.ifconfig_button = tk.Button(
            utils_frame, text="네트워크 정보 조회", command=self.show_ifconfig_info
        )
        self.ifconfig_button.pack()
        self.ifconfig_text = scrolledtext.ScrolledText(
            utils_frame, wrap=tk.WORD, width=50, height=10, state="disabled"
        )
        self.ifconfig_text.pack(pady=5)

        # 바이트 순서 변환
        byte_frame = tk.LabelFrame(utils_frame, text="바이트 순서 변환", padx=5, pady=5)
        byte_frame.pack(fill=tk.X, pady=5)
        tk.Label(byte_frame, text="변환할 정수 입력:").pack()
        self.byte_order_entry = tk.Entry(byte_frame)
        self.byte_order_entry.pack(fill=tk.X)
        tk.Button(
            byte_frame, text="변환", command=self.show_byte_order_conversion
        ).pack(pady=5)
        self.byte_order_result = scrolledtext.ScrolledText(
            byte_frame, height=4, wrap=tk.WORD, state="disabled"
        )
        self.byte_order_result.pack(fill=tk.X)

        # IP 변환
        ip_frame = tk.LabelFrame(utils_frame, text="IP 주소 변환", padx=5, pady=5)
        ip_frame.pack(fill=tk.X, pady=5)
        tk.Label(ip_frame, text="IP 주소 입력:").pack()
        ip_entry_frame = tk.Frame(ip_frame)
        ip_entry_frame.pack(fill=tk.X)
        self.ip_blocks = []
        for i in range(4):
            block = tk.Entry(ip_entry_frame, width=3, validate="key")
            block.pack(side=tk.LEFT)
            if i < 3:
                tk.Label(ip_entry_frame, text=".").pack(side=tk.LEFT)
            self.ip_blocks.append(block)
        tk.Button(ip_frame, text="변환", command=self.show_ip_conversion).pack(pady=5)
        self.ip_result_text = scrolledtext.ScrolledText(
            ip_frame, height=3, wrap=tk.WORD, state="disabled"
        )
        self.ip_result_text.pack(fill=tk.X)

        # DNS 조회
        dns_frame = tk.LabelFrame(utils_frame, text="DNS 조회", padx=5, pady=5)
        dns_frame.pack(fill=tk.X, pady=5)
        tk.Label(dns_frame, text="도메인 입력:").pack()
        self.dns_entry = tk.Entry(dns_frame)
        self.dns_entry.pack(fill=tk.X)
        tk.Button(dns_frame, text="조회", command=self.show_dns_conversion).pack(pady=5)
        self.dns_result_text = scrolledtext.ScrolledText(
            dns_frame, height=3, wrap=tk.WORD, state="disabled"
        )
        self.dns_result_text.pack(fill=tk.X)

        # 공유 캔버스 영역을 새로운 컬럼(column=2)에 배치
        canvas_frame = tk.LabelFrame(master, text="공유 캔버스", padx=5, pady=5)
        canvas_frame.grid(row=0, column=2, sticky="nsew", padx=5, pady=5)

        self.canvas = tk.Canvas(canvas_frame, width=400, height=300, bg="white")
        self.canvas.pack(side=tk.TOP, pady=5)

        self.clear_button = tk.Button(
            canvas_frame, text="Clear", command=self.clear_canvas, state="disabled"
        )
        self.clear_button.pack(side=tk.BOTTOM, pady=5)

        # 디버그용 텍스트 영역 추가
        self.debug_text = tk.Text(canvas_frame, height=5, state="disabled")
        self.debug_text.pack(side=tk.BOTTOM, fill=tk.X, pady=5)

        # netstat 영역은 아래쪽(row=1)에 3컬럼을 모두 사용하도록 설정
        netstat_frame = tk.LabelFrame(master, text="포트 상태(netstat)", padx=5, pady=5)
        netstat_frame.grid(row=1, column=0, columnspan=3, sticky="nsew", padx=5, pady=5)

        self.netstat_text = scrolledtext.ScrolledText(
            netstat_frame, width=100, height=10, state="disabled"
        )
        self.netstat_text.pack(pady=(0, 5))

        self.netstat_button = tk.Button(
            netstat_frame, text="netstat 조회", command=self.show_netstat_info
        )
        self.netstat_button.pack()

        self.drawing = False
        self.local_last_x = None  # 로컬 드로잉용 변수
        self.local_last_y = None
        self.last_x = None  # 원격 드로잉용 변수
        self.last_y = None

        # Grid 설정 (3 컬럼 레이아웃)
        master.grid_columnconfigure(0, weight=1)
        master.grid_columnconfigure(1, weight=1)
        master.grid_columnconfigure(2, weight=1)
        master.grid_rowconfigure(0, weight=1)
        master.grid_rowconfigure(1, weight=0)

    def validate_ip_block(self, value):
        if value.isdigit() and 0 <= int(value) <= 255:
            return True
        elif value == "":
            return True
        else:
            return False

    def connect_server(self):
        if self.client.connect_to_server():
            self.update_connection_buttons(True)
            self.enable_canvas()

    def disconnect_server(self):
        self.client.disconnect()
        self.update_connection_buttons(False)
        self.disable_canvas()

    def update_connection_buttons(self, is_connected):
        if is_connected:
            self.connect_button.config(state="disabled")
            self.disconnect_button.config(state="normal")
        else:
            self.connect_button.config(state="normal")
            self.disconnect_button.config(state="disabled")

    def enable_canvas(self):
        self.canvas.bind("<Button-1>", self.start_draw)
        self.canvas.bind("<B1-Motion>", self.draw)
        self.canvas.bind("<ButtonRelease-1>", self.stop_draw)
        self.clear_button.config(state="normal")

    def disable_canvas(self):
        self.canvas.unbind("<Button-1>")
        self.canvas.unbind("<B1-Motion>")
        self.canvas.unbind("<ButtonRelease-1>")
        self.clear_button.config(state="disabled")

    def send_message(self, event=None):
        message = self.entry_message.get().strip()
        if message:
            if self.client.send_message(message):
                self.entry_message.delete(0, tk.END)
            self.entry_message.delete(0, tk.END)

    def start_draw(self, event):
        self.drawing = True
        self.local_last_x, self.local_last_y = event.x, event.y
        self.client.send_draw_event("start", event.x, event.y)
        self.log_debug(f"start_draw at ({event.x}, {event.y})")

    def draw(self, event):
        if self.drawing:
            # 이전 좌표와 현재 좌표를 연결하는 선 그리기
            self.canvas.create_line(
                self.local_last_x,
                self.local_last_y,
                event.x,
                event.y,
                fill="black",
                width=2,
            )
            self.client.send_draw_event("move", event.x, event.y)
            self.log_debug(f"draw at ({event.x}, {event.y})")
            self.local_last_x, self.local_last_y = event.x, event.y

    def stop_draw(self, event):
        if self.drawing:
            self.drawing = False
            self.client.send_draw_event("end", event.x, event.y)
            self.log_debug(f"stop_draw at ({event.x}, {event.y})")

    def handle_draw_event(self, event_data):
        x, y = event_data["x"], event_data["y"]
        if event_data["action"] == "start":
            self.last_x = x
            self.last_y = y
        elif event_data["action"] == "move" and self.last_x is not None:
            # 이전 좌표와 현재 좌표를 연결하는 선 그리기
            self.canvas.create_line(
                self.last_x, self.last_y, x, y, fill="black", width=2
            )
            self.last_x = x
            self.last_y = y
        elif event_data["action"] == "end":
            self.last_x = None
            self.last_y = None

    def clear_canvas(self):
        self.canvas.delete("all")
        self.client.send_clear_event()

    def handle_clear_event(self):
        self.canvas.delete("all")

    def append_message(self, msg):
        self.chat_area.config(state="normal")
        self.chat_area.insert(tk.END, msg + "\n")
        self.chat_area.see(tk.END)
        self.chat_area.config(state="disabled")
        print(msg)

    def log_message(self, msg):
        print(msg)
        if self.gui:
            self.gui.status_label.config(text=msg)

    def log_debug(self, message):
        self.debug_text.config(state="normal")
        self.debug_text.insert(tk.END, message + "\n")
        self.debug_text.see(tk.END)
        self.debug_text.config(state="disabled")
        print(message)

    # 네트워크 정보 관련 메서드
    def show_ifconfig_info(self):
        info = get_ifconfig_info()
        self.ifconfig_text.config(state="normal")
        self.ifconfig_text.delete("1.0", tk.END)
        self.ifconfig_text.insert(tk.END, info)
        self.ifconfig_text.config(state="disabled")

    def show_byte_order_conversion(self):
        try:
            value = int(self.byte_order_entry.get())
            result = convert_byte_order(value)
            self.byte_order_result.config(state="normal")
            self.byte_order_result.delete("1.0", tk.END)
            self.byte_order_result.insert(tk.END, result)
            self.byte_order_result.config(state="disabled")
        except ValueError:
            self.byte_order_result.config(state="normal")
            self.byte_order_result.delete("1.0", tk.END)
            self.byte_order_result.insert(tk.END, "올바른 정수를 입력하세요")
            self.byte_order_result.config(state="disabled")

    def show_ip_conversion(self):
        ip = ".".join(block.get() for block in self.ip_blocks)
        result = convert_ip_address(ip)
        self.ip_result_text.config(state="normal")
        self.ip_result_text.delete("1.0", tk.END)
        self.ip_result_text.insert(tk.END, result)
        self.ip_result_text.config(state="disabled")

    def show_dns_conversion(self):
        domain = self.dns_entry.get()
        result = dns_lookup(domain)
        self.dns_result_text.config(state="normal")
        self.dns_result_text.delete("1.0", tk.END)
        self.dns_result_text.insert(tk.END, result)
        self.dns_result_text.config(state="disabled")

    def show_netstat_info(self):
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

        self.netstat_text.config(state="normal")
        self.netstat_text.delete("1.0", tk.END)
        self.netstat_text.insert(tk.END, filtered_info)
        self.netstat_text.config(state="disabled")


if __name__ == "__main__":

    def on_closing():
        if client:
            client.disconnect()
        root.destroy()

    root = tk.Tk()
    client = ChatClient(host="127.0.0.1", port=9000)
    gui = ClientGUI(root, client)
    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()
