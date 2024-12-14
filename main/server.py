import socket
import threading
import tkinter as tk
import json
from tkinter import scrolledtext
from network_utils import get_netstat_info


class ChatServer:
    def __init__(self, host="0.0.0.0", port=9000):
        self.host = host
        self.port = port
        self.clients = []
        self.client_names = {}
        self.server_socket = None
        self.gui = None
        self.running = False
        self.user_count = 0
        self.drawing_events = []  # 모든 드로잉 이벤트 저장

    def accept_clients(self):
        while self.running:
            try:
                client_socket, addr = self.server_socket.accept()
                self.clients.append(client_socket)
                self.user_count += 1
                username = f"User{self.user_count}"
                self.client_names[client_socket] = username

                self.log_message(f"{username} 접속: {addr}")
                # 새로운 사용자 접속을 모든 클라이언트에게 알림
                self.broadcast_message(f"### {username} 접속 ###")
                threading.Thread(
                    target=self.handle_client, args=(client_socket,), daemon=True
                ).start()
                self.update_client_count()
                self.refresh_netstat()
                # 새 클라이언트에게 현재까지의 그리기 데이터 전송
                if self.drawing_events:
                    try:
                        for event in self.drawing_events:
                            message = json.dumps(event) + "\n"
                            client_socket.sendall(message.encode("utf-8"))
                    except:
                        pass
            except:
                break

    def handle_client(self, client_socket):
        username = self.client_names.get(client_socket, "Unknown")

        buffer = ""
        while self.running:
            try:
                data = client_socket.recv(1024)
                if not data:
                    break
                buffer += data.decode("utf-8")
                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    if not line.strip():
                        continue
                    try:
                        # JSON 메시지 파싱 시도
                        message = json.loads(line)
                        if isinstance(message, dict) and "type" in message:
                            if message["type"] in ["draw", "clear"]:
                                # 드로잉 이벤트 저장 및 브로드캐스트
                                if message["type"] == "clear":
                                    self.drawing_events.clear()
                                else:
                                    self.drawing_events.append(message)
                                self.broadcast_message(line, exclude=None)
                                continue
                    except json.JSONDecodeError:
                        pass
                    # 일반 채팅 메시지 처리
                    message = line
                    send_msg = f"[{username}] {message}"
                    self.broadcast_message(send_msg, exclude=client_socket)
                    self.log_message(send_msg)
            except:
                break
        self.remove_client(client_socket)

    def broadcast_message(self, message, exclude=None):
        message += "\n"  # 메시지 구분을 위한 개행 추가
        encoded_message = message.encode("utf-8")
        for c in self.clients[:]:
            if c != exclude:
                try:
                    c.sendall(encoded_message)
                except:
                    self.remove_client(c)

    def remove_client(self, client_socket):
        if client_socket in self.clients:
            self.clients.remove(client_socket)
            uname = self.client_names.pop(client_socket, "Unknown")
            client_socket.close()
            self.log_message(f"{uname} 퇴장")
            # 사용자 퇴장을 모든 클라이언트에게 알림
            self.broadcast_message(f"### {uname} 퇴장 ###")
            self.update_client_count()
            self.refresh_netstat()

    def stop_server(self):
        self.running = False
        # 모든 클라이언트에게 서버 종료 메시지 전송
        self.broadcast_message("### 서버가 종료되었습니다 ###")
        for c in self.clients[:]:
            try:
                c.close()
            except:
                pass
        self.clients.clear()
        self.client_names.clear()
        if self.server_socket:
            try:
                self.server_socket.shutdown(socket.SHUT_RDWR)
                self.server_socket.close()
            except:
                pass
        self.server_socket = None
        self.log_message("서버 중지")
        self.update_client_count()
        self.refresh_netstat()

    def start_server(self):
        if not self.running:
            try:
                self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                self.server_socket.bind((self.host, self.port))
                self.server_socket.listen()
                self.running = True
                self.log_message(f"서버 시작: {self.host}:{self.port}")
                threading.Thread(target=self.accept_clients, daemon=True).start()
                self.refresh_netstat()
            except OSError as e:
                self.log_message(f"서버 시작 실패: {e}")
                if self.server_socket:
                    self.server_socket.close()
                self.running = False

    def update_client_count(self):
        if self.gui:
            self.gui.client_count_label.config(
                text=f"현재 클라이언트 수: {len(self.clients)}"
            )

    def log_message(self, msg):
        if self.gui:
            self.gui.log_area.config(state="normal")
            self.gui.log_area.insert(tk.END, msg + "\n")
            self.gui.log_area.see(tk.END)
            self.gui.log_area.config(state="disabled")
        print(msg)

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

        # --- netstat 결과 표시를 위한 UI 추가 ---
        netstat_frame = tk.LabelFrame(master, text="포트 상태(netstat)", padx=5, pady=5)
        netstat_frame.grid(row=0, column=1, rowspan=3, padx=10, pady=10, sticky="n")

        self.netstat_text = scrolledtext.ScrolledText(
            netstat_frame, width=60, height=20
        )
        self.netstat_text.pack(pady=(0, 5))

        self.netstat_button = tk.Button(
            netstat_frame, text="netstat 조회", command=self.show_netstat_info
        )
        self.netstat_button.pack()

        # Grid 설정
        master.grid_columnconfigure(0, weight=1)
        master.grid_columnconfigure(1, weight=1)

    def show_netstat_info(self):
        port = self.server.port
        info = get_netstat_info(port)
        self.netstat_text.delete("1.0", tk.END)
        self.netstat_text.insert(tk.END, info)

    def start_server(self):
        self.server.start_server()
        self.start_button.config(state="disabled")
        self.stop_button.config(state="normal")

    def stop_server(self):
        self.server.stop_server()
        self.start_button.config(state="normal")
        self.stop_button.config(state="disabled")


if __name__ == "__main__":
    # 메인 윈도우가 닫힐 때 서버 종료를 보장하기 위한 함수
    def on_closing():
        if server:
            server.stop_server()
        root.destroy()

    root = tk.Tk()
    server = ChatServer(host="0.0.0.0", port=9000)
    gui = ServerGUI(root, server)
    root.protocol("WM_DELETE_WINDOW", on_closing)  # 창 닫기 이벤트 처리
    root.mainloop()
