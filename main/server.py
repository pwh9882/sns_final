import socket
import threading
import tkinter as tk
from tkinter import scrolledtext


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
            except:
                break

    def handle_client(self, client_socket):
        username = self.client_names.get(client_socket, "Unknown")
        while self.running:
            try:
                data = client_socket.recv(1024)
                if not data:
                    break
                message = data.decode("utf-8")
                # 받은 메시지를 다른 클라이언트에게 브로드캐스트
                send_msg = f"[{username}] {message}"
                self.broadcast_message(send_msg, exclude=client_socket)
                self.log_message(send_msg)
            except:
                break
        self.remove_client(client_socket)

    def broadcast_message(self, message, exclude=None):
        for c in self.clients[:]:
            if c != exclude:
                try:
                    c.sendall(message.encode("utf-8"))
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


class ServerGUI:
    def __init__(self, master, server: ChatServer):
        self.master = master
        self.server = server
        self.server.gui = self

        master.title("서버 GUI")

        self.log_area = scrolledtext.ScrolledText(
            master, state="disabled", width=50, height=20
        )
        self.log_area.grid(row=0, column=0, padx=10, pady=10)

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
