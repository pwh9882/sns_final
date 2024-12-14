import socket
import threading
import tkinter as tk
from tkinter import scrolledtext


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

        master.title("클라이언트 GUI")

        self.chat_area = scrolledtext.ScrolledText(
            master, state="disabled", width=50, height=20
        )
        self.chat_area.grid(row=0, column=0, columnspan=2, padx=10, pady=10)

        self.entry_message = tk.Entry(master, width=40)
        self.entry_message.grid(row=1, column=0, padx=10, sticky="w")
        self.send_button = tk.Button(master, text="전송", command=self.send_message)
        self.send_button.grid(row=1, column=1, sticky="e", padx=10)

        frame_buttons = tk.Frame(master)
        frame_buttons.grid(row=2, column=0, columnspan=2, pady=5)

        self.connect_button = tk.Button(
            frame_buttons, text="서버 접속", command=self.connect_server
        )
        self.connect_button.pack(side=tk.LEFT, padx=5)

        self.disconnect_button = tk.Button(
            frame_buttons,
            text="접속 해제",
            command=self.disconnect_server,
            state="disabled",
        )
        self.disconnect_button.pack(side=tk.LEFT, padx=5)

        self.status_label = tk.Label(master, text="서버에 연결되지 않음")
        self.status_label.grid(row=3, column=0, columnspan=2, pady=5)

        self.entry_message.bind("<Return>", lambda e: self.send_message())

    def connect_server(self):
        self.client.connect_to_server()
        if self.client.running:
            self.update_connection_buttons(True)

    def disconnect_server(self):
        self.client.disconnect()
        self.update_connection_buttons(False)

    # 새로운 메서드 추가
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
