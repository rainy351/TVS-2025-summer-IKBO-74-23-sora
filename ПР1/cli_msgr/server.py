import socket
import threading
import time

class ChatServer:
    def __init__(self, host='localhost', port=12345):
        self.host = host
        self.port = port
        self.clients = {}  # {socket: {'nickname': '', 'address': ''}}
        self.online_users = []
        self.user_database = {}  # {nickname: password}
        self.server_socket = None
        self.running = True
        self.history = []
        
    def start(self):
        """Запуск сервера"""
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        
        print(f"Сервер запущен на {self.host}:{self.port}")
        print("Ожидание подключений...")
        
        try:
            while self.running:
                client_socket, address = self.server_socket.accept()
                print(f"Новое подключение от {address}")
                
                client_thread = threading.Thread(
                    target=self.handle_client,
                    args=(client_socket, address)
                )
                client_thread.daemon = True
                client_thread.start()
                
        except KeyboardInterrupt:
            print("\nОстановка сервера...")
        finally:
            self.stop()
    
    def handle_client(self, client_socket, address):
        """Обработка клиентского соединения"""
        try:
            authenticated = False
            nickname = None
            password = None
            
            while not authenticated:
                data = client_socket.recv(1024).decode('utf-8')
                if not data:
                    break
                
                if data.startswith('REGISTER:'):
                    # REGISTER:nickname:password
                    _, nickname, password = data.split(':', 2)
                    
                    # if nickname in self.user_database:
                    #     client_socket.send("USER_EXISTS".encode('utf-8'))
                    #     continue
                    
                    self.user_database[nickname] = password
                    self.clients[client_socket] = {
                        'nickname': nickname,
                        'address': address,
                        'password': password
                    }
                    self.online_users.append(nickname)
                    authenticated = True
                    client_socket.send("REGISTER_SUCCESS".encode('utf-8'))
                    print(f"Пользователь {nickname} зарегистрирован и вошел")
                    
                elif data.startswith('LOGIN:'):
                    # LOGIN:nickname:password
                    _, nickname, password = data.split(':', 2)
                    
                    if nickname not in self.user_database:
                        client_socket.send("USER_NOT_FOUND".encode('utf-8'))
                        continue
                    
                    if self.user_database[nickname] != password:
                        client_socket.send("WRONG_PASSWORD".encode('utf-8'))
                        continue
                    
                    self.clients[client_socket] = {
                        'nickname': nickname,
                        'address': address,
                        'password': password
                    }
                    self.online_users.append(nickname)
                    authenticated = True
                    client_socket.send("LOGIN_SUCCESS".encode('utf-8'))
                    print(f"Пользователь {nickname} вошел в систему")
                    
                else:
                    client_socket.send("INVALID_COMMAND".encode('utf-8'))
            
            if not authenticated:
                return
            
            # Отправляем приветственное сообщение
            welcome_msg = "[YLW]:\n~[WELCOME TO EASY_CHAT]~\n"
            client_socket.send(welcome_msg.encode('utf-8'))
            
            welcome_msg2 = f"[GRN]:Добро пожаловать в чат, {nickname}! Сейчас онлайн: {len(self.online_users)}\n(Напишите /? для помощи)\n"
            client_socket.send(welcome_msg2.encode('utf-8'))
            
            # Отправляем историю чата
            if len(self.history) > 0:
                hist = "[GRY]:# Последние сообщения #\n" + "\n".join(self.history[-10:])
                client_socket.send(hist.encode('utf-8'))
            
            # Уведомляем всех о новом пользователе
            self.broadcast(f"[GRN]:{nickname} присоединился к чату!", exclude=client_socket)
            
            # Основной цикл обработки сообщений
            while authenticated:
                try:
                    data = client_socket.recv(1024).decode('utf-8')
                    if not data:
                        break
                    
                    if data == '/quit':
                        # Удаляем пользователя из списка онлайн при выходе
                        self.remove_user_from_online(nickname)
                        break
                        
                    elif data == '/online':
                        online_list = ", ".join(self.online_users)
                        client_socket.send(f"[GRN]:Онлайн ({len(self.online_users)}): {online_list}".encode('utf-8'))
                        
                    else:
                        # Отправляем сообщение всем
                        message = f"{nickname}: {data}"
                        self.history.append(f"{message}")
                        self.broadcast(message, exclude=client_socket)
                        
                except ConnectionResetError:
                    break
                    
        except Exception as e:
            print(f"Ошибка обработки клиента {address}: {e}")
        finally:
            # Удаляем клиента при отключении
            self.remove_client(client_socket, nickname)
    
    def remove_user_from_online(self, nickname):
        """Удаление пользователя из списка онлайн"""
        # Удаляем только одно вхождение (первое найденное)
        for i, user in enumerate(self.online_users):
            if user == nickname:
                self.online_users.pop(i)
                break
        print(f"Пользователь {nickname} удален из списка онлайн")
    
    def broadcast(self, message, exclude=None):
        """Отправка сообщения всем клиентам"""
        for client_socket in self.clients.keys():
            if client_socket != exclude:
                try:
                    client_socket.send(message.encode('utf-8'))
                except Exception:
                    nickname = self.clients[client_socket]['nickname']
                    self.remove_client(client_socket, nickname)
    
    def remove_client(self, client_socket, nickname=None):
        """Удаление клиента"""
        if client_socket in self.clients:
            if nickname is None:
                nickname = self.clients[client_socket]['nickname']
            
            self.clients.pop(client_socket, None)
            
            # if nickname:
            #     self.remove_user_from_online(nickname)
            
            print(f"Пользователь {nickname} отключился")
            
            try:
                client_socket.close()
            except Exception:
                pass
    
    def stop(self):
        """Остановка сервера"""
        self.running = False
        for client_socket in self.clients.keys():
            nickname = self.clients[client_socket]['nickname']
            self.remove_client(client_socket, nickname)
        
        if self.server_socket:
            self.server_socket.close()
        print("Сервер остановлен")

if __name__ == "__main__":
    server = ChatServer()
    server.start()