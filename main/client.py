import socket
import threading
import tkinter as tk
from tkinter import scrolledtext
from network_utils import (
    get_ifconfig_info,
    convert_byte_order,
    convert_ip_address,
    dns_lookup,
)


class ChatClient:
    def __init__(self, host="127.0.0.1", port=9000):
        self.host = host
        self.port = port
        self.client_socket = None
        self.gui = None
        self.running = False

    def connect_to_server(self):
        if not self.running:
            try:
                self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.client_socket.connect((self.host, self.port))
                self.running = True
                self.log_message("서버에 연결되었습니다.")
                threading.Thread(target=self.receive_messages, daemon=True).start()
                return True
            except Exception as e:
                self.log_message(f"서버 접속 실패: {e}")
                if self.client_socket:
                    self.client_socket.close()
                self.client_socket = None
                return False

    def receive_messages(self):
        while self.running:
            try:
                data = self.client_socket.recv(1024)
                if not data:
                    break
                message = data.decode("utf-8")
                self.append_message(message)
            except:
                break
        self.log_message("서버와의 연결이 종료되었습니다.")
        self.running = False
        # GUI 버튼 상태 업데이트
        if self.gui:
            self.gui.update_connection_buttons(False)

    def send_message(self, message):
        if self.running and message.strip():
            try:
                self.client_socket.sendall(message.encode("utf-8"))
                self.append_message(f"나: {message}")  # 자신의 메시지를 GUI에 추가
                return True
            except:
                self.log_message("메시지 전송 실패")
                self.disconnect()
                return False

    def append_message(self, msg):
        if self.gui:
            self.gui.chat_area.config(state="normal")
            self.gui.chat_area.insert(tk.END, msg + "\n")
            self.gui.chat_area.see(tk.END)
            self.gui.chat_area.config(state="disabled")
        print(msg)

    def log_message(self, msg):
        print(msg)
        if self.gui:
            self.gui.status_label.config(text=msg)

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

        # ifconfig 정보
        tk.Label(utils_frame, text="시스템 네트워크 정보").pack(pady=(0, 5))
        self.ifconfig_button = tk.Button(
            utils_frame, text="네트워크 정보 조회", command=self.show_ifconfig_info
        )
        self.ifconfig_button.pack()
        self.ifconfig_text = scrolledtext.ScrolledText(
            utils_frame, wrap=tk.WORD, width=50, height=10
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
        self.byte_order_result = tk.Label(byte_frame, text="", wraplength=200)
        self.byte_order_result.pack()

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

        for block in self.ip_blocks:
            block.config(
                validate="key",
                validatecommand=(master.register(self.validate_ip_block), "%P"),
            )

        tk.Button(ip_frame, text="변환", command=self.show_ip_conversion).pack(pady=5)
        self.ip_result_label = tk.Label(ip_frame, text="", wraplength=200)
        self.ip_result_label.pack()

        # DNS 조회
        dns_frame = tk.LabelFrame(utils_frame, text="DNS 조회", padx=5, pady=5)
        dns_frame.pack(fill=tk.X, pady=5)

        tk.Label(dns_frame, text="도메인 입력:").pack()
        self.dns_entry = tk.Entry(dns_frame)
        self.dns_entry.pack(fill=tk.X)
        tk.Button(dns_frame, text="조회", command=self.show_dns_conversion).pack(pady=5)
        self.dns_result_label = tk.Label(dns_frame, text="", wraplength=200)
        self.dns_result_label.pack()

        # Grid 설정
        master.grid_columnconfigure(0, weight=1)
        master.grid_columnconfigure(1, weight=1)
        master.grid_rowconfigure(0, weight=1)

    def validate_ip_block(self, value):
        if value.isdigit() and 0 <= int(value) <= 255:
            return True
        elif value == "":
            return True
        else:
            return False

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

    def send_message(self):
        message = self.entry_message.get().strip()
        if message:
            if self.client.send_message(message):
                self.entry_message.delete(0, tk.END)
            # 성공 여부와 관계없이 입력 필드를 비웁니다.
            self.entry_message.delete(0, tk.END)

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

    # 네트워크 정보 관련 메서드
    def show_ifconfig_info(self):
        info = get_ifconfig_info()
        self.ifconfig_text.delete("1.0", tk.END)
        self.ifconfig_text.insert(tk.END, info)

    def show_byte_order_conversion(self):
        try:
            value = int(self.byte_order_entry.get())
            result = convert_byte_order(value)
            self.byte_order_result.config(text=result)
        except ValueError:
            self.byte_order_result.config(text="올바른 정수를 입력하세요")

    def show_ip_conversion(self):
        ip = ".".join(block.get() for block in self.ip_blocks)
        result = convert_ip_address(ip)
        self.ip_result_label.config(text=result)

    def show_dns_conversion(self):
        domain = self.dns_entry.get()
        result = dns_lookup(domain)
        self.dns_result_label.config(text=result)


if __name__ == "__main__":
    # 메인 윈도우가 닫힐 때 클라이언트 종료를 보장하기 위한 함수
    def on_closing():
        if client:
            client.disconnect()
        root.destroy()

    root = tk.Tk()
    client = ChatClient(host="127.0.0.1", port=9000)
    gui = ClientGUI(root, client)
    root.protocol("WM_DELETE_WINDOW", on_closing)  # 창 닫기 이벤트 처리
    root.mainloop()
