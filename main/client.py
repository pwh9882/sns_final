import socket
import threading
import tkinter as tk
from tkinter import scrolledtext


class ChatClient:
    def __init__(self, host="127.0.0.1", port=5000):
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
                message = data.decode("utf-8")
                self.append_message(message)
            except:
                break
        self.log_message("서버와의 연결이 종료되었습니다.")
        self.running = False

    def send_message(self, message):
        if self.running and message.strip():
            self.client_socket.sendall(message.encode("utf-8"))
            self.append_message(f"(나) {message}")

    def append_message(self, msg):
        if self.gui:
            self.gui.chat_area.config(state="normal")
            self.gui.chat_area.insert(tk.END, msg + "\n")
            self.gui.chat_area.see(tk.END)
            self.gui.chat_area.config(state="disabled")
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
        self.chat_area = scrolledtext.ScrolledText(
            master, state="disabled", width=50, height=20
        )
        self.chat_area.grid(row=0, column=0, padx=10, pady=10)

        # 메시지 입력
        self.entry_message = tk.Entry(master, width=40)
        self.entry_message.grid(row=1, column=0, padx=10, sticky="w")
        self.send_button = tk.Button(master, text="전송", command=self.send_message)
        self.send_button.grid(row=1, column=0, sticky="e", padx=10)

        # 서버 접속/해제 버튼
        self.connect_button = tk.Button(
            master, text="서버 접속", command=self.connect_server
        )
        self.connect_button.grid(row=2, column=0, sticky="w", padx=10, pady=5)
        self.disconnect_button = tk.Button(
            master, text="접속 해제", command=self.disconnect_server
        )
        self.disconnect_button.grid(row=2, column=0, sticky="e", padx=10, pady=5)

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
    client = ChatClient(host="127.0.0.1", port=5000)
    gui = ClientGUI(root, client)
    root.mainloop()
