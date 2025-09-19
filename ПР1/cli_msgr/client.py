import socket
import threading
import sys
from utils import process_colored_message

             
class SimpleChatClient:
    def __init__(self, host='localhost', port=12345):
        self.host = host
        self.port = port
        self.socket = None
        self.nickname = None
        self.running = False
        self.input_active = False
    
    def connect(self):
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.host, self.port))
            self.running = True
            return True
        except Exception as e:
            print(f"Ошибка подключения: {e}")
            return False
    
    def authenticate(self):
        print("=== ВХОД ===")
        action = input("Регистрация (1) или Вход (2): ").strip()
        
        nickname = input("Логин: ").strip()
        password = input("Пароль: ").strip()
        
        if action == '1':
            self.socket.send(f"REGISTER:{nickname}:{password}".encode('utf-8'))
        else:
            self.socket.send(f"LOGIN:{nickname}:{password}".encode('utf-8'))
        
        response = self.socket.recv(1024).decode('utf-8')
        if response in ["REGISTER_SUCCESS", "LOGIN_SUCCESS"]:
            self.nickname = nickname
            print("Успешная авторизация!")
            return True
        print("Ошибка авторизации")
        return False
    
    def listen_server(self):
        while self.running:
            try:
                msg = self.socket.recv(1024).decode('utf-8')
                if not msg:
                    break
                
                if self.input_active:
                    sys.stdout.write('\r')
                
                if "]:" in msg:
                    process_colored_message(msg)
                else:
                    print(msg)
                
                if self.input_active:
                    sys.stdout.write(f"{self.nickname}: ")
                    sys.stdout.flush()
                    
            except Exception:
                break
    
    def run(self):
        if not self.connect() or not self.authenticate():
            return
        
        listener = threading.Thread(target=self.listen_server, daemon=True)
        listener.start()
        
        while self.running:
            try:
                self.input_active = True
                sys.stdout.write(f"{self.nickname}: ")
                sys.stdout.flush()
                
                msg = sys.stdin.readline().strip()
                self.input_active = False
                
                if msg == '/quit':
                    process_colored_message("[RED]:Выход...")
                    self.socket.send('/quit'.encode('utf-8'))
                    break
                elif msg == '/online':
                    self.socket.send('/online'.encode('utf-8'))
                elif msg == '/?':
                    process_colored_message("[GRN]:Команды: /online, /quit")
                elif msg:
                    self.socket.send(msg.encode('utf-8'))
                    
            except (KeyboardInterrupt, EOFError):
                print("\nВыход...")
                break
        
        self.running = False
        self.socket.close()
        print("Отключено")

if __name__ == "__main__":
    client = SimpleChatClient()
    client.run()