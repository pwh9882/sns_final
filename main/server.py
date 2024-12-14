import socket
import threading
import tkinter as tk
from tkinter import scrolledtext


class ChatServer:
    def __init__(self, host="0.0.0.0", port=5000):
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
            threading.Thread(
                target=self.handle_client, args=(client_socket,), daemon=True
            ).start()
            self.update_client_count()

    def handle_client(self, client_socket):
        while self.running:
            try:
                data = client_socket.recv(1024)
                if not data:
                    break
                message = data.decode("utf-8")
                self.broadcast_message(message, exclude=client_socket)
                self.log_message(f"[클라이언트] {message}")
            except:
                break
        self.remove_client(client_socket)

    def broadcast_message(self, message, exclude=None):
        for c in self.clients:
            if c != exclude:
                try:
                    c.sendall(message.encode("utf-8"))
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

        # 로그 출력 영역
        self.log_area = scrolledtext.ScrolledText(
            master, state="disabled", width=50, height=20
        )
        self.log_area.grid(row=0, column=0, padx=10, pady=10)

        # 클라이언트 수 표시 레이블
        self.client_count_label = tk.Label(master, text="현재 클라이언트 수: 0")
        self.client_count_label.grid(row=1, column=0, sticky="w", padx=10)

        # 서버 제어 버튼
        self.start_button = tk.Button(
            master, text="서버 시작", command=self.start_server
        )
        self.start_button.grid(row=2, column=0, sticky="w", padx=10, pady=5)
        self.stop_button = tk.Button(master, text="서버 중지", command=self.stop_server)
        self.stop_button.grid(row=2, column=0, sticky="e", padx=10, pady=5)

    def start_server(self):
        self.server.start_server()

    def stop_server(self):
        self.server.stop_server()


if __name__ == "__main__":
    root = tk.Tk()
    server = ChatServer(host="0.0.0.0", port=5000)
    gui = ServerGUI(root, server)
    root.mainloop()
