import socket
import json
from threading import Thread


class XenoTable:
    def __init__(self, ip: str, port: int):
        self.__connection = socket.socket()
        self.__connection.settimeout(5)  # Set a 5-second timeout for this socket operation
        print(f"Attempting to connect to {ip}:{port}")
        try:
            self.__connection.connect((ip, port))
            print("Connection successful")
        except socket.timeout as e:
            print(f"Connection timed out: {e}")
            raise ConnectionError(f"Connection to {ip}:{port} timed out - {e}")
        except socket.error as e:
            print(f"Connection failed: {e}")
            raise ConnectionError(f"Failed to connect to {ip}:{port} - {e}")
        self.ip = ip
        self.port = port
        self.recv(1)

    def save(self, string: str) -> bool:
        self.send(f"S*{string}*")
        return self.recv(1)[0] == "true"

    def load(self, string: str) -> bool:
        self.send(f"L*{string}*")
        return self.recv(1)[0] == "true"

    def run(self, msg: str) -> None:
        self.send(f"R*{msg}*")

    def recv(self, limit: int) -> list:
        command = ""
        num = 0
        try:
            while True:
                char = self.__connection.recv(1).decode("UTF-8")
                if char == "*":
                    num += 1
                    if num == limit:
                        break
                command += char
        except socket.error as e:
            raise ConnectionError(f"Socket error occurred: {e}")
        return command.split("*")

    def send(self, msg: str) -> None:
        try:
            self.__connection.send(msg.encode("UTF-8"))
        except socket.error as e:
            raise ConnectionError(f"Socket error occurred: {e}")

    @property
    def ping(self) -> bool:
        self.send("I*")
        self.recv(1)
        return True

    def put(self, name: str, val: object) -> None:
        illegals = ["*", "\\", "/"]
        val_str = json.dumps(val)
        check = [name, val_str]
        names = ["Identifier", "Value"]
        for item in range(len(check)):
            for ill in illegals:
                if ill in check[item]:
                    raise ValueError(f"{names[item]} cannot contain {ill}")
        self.send(f"P*{name}*{val_str}*")

    def get(self, name: str) -> object:
        if "*" in name:
            raise ValueError("Identifier cannot contain *")
        self.send(f"G*{name}*")
        command = self.recv(1)
        if command[0] == "KeyError":
            raise KeyError("The data for the given key was not found")
        else:
            return json.loads(command[0])

    def get_all(self) -> dict:
        data = self.get("../")
        if not isinstance(data, dict):
            raise TypeError("Expected data to be a dictionary")
        return data

    def pop(self, name: str) -> object:
        self.send(f"O*{name}*")
        command = self.recv(1)
        if command[0] == "KeyError":
            raise KeyError("The data for the given key was not found")
        else:
            return json.loads(command[0])

    def get_callable(self, name: str, call: str) -> object:
        if "*" in name or "*" in call:
            raise ValueError("Identifier and Call cannot contain *")
        self.send(f"M*{name}*{call}*")
        command = self.recv(1)
        if command[0] == "KeyError":
            raise KeyError("The data for the given key was not found")
        elif command[0] == "IndexError":
            raise IndexError("list index out of range")
        elif command[0] == "TypeError":
            raise TypeError("Object not subscriptable")
        elif command[0] == "SyntaxError":
            raise SyntaxError("invalid syntax")
        else:
            return json.loads(command[0])

    def append(self, name: str, data: object) -> None:
        self.send(f"A*{name}*{json.dumps(data)}*")
        command = self.recv(1)
        if command[0] == "AttributeError":
            raise AttributeError("Data has no attribute 'append'")

    def get_new_table(self) -> 'XenoTable':
        self.send("N*")
        command = ""
        while True:
            char = self.__connection.recv(1).decode("UTF-8")
            if char == "*":
                break
            command += char
        return XenoTable(self.ip, int(command))

    def close_server(self) -> None:
        self.send("C*close*")
        self.__connection.close()

    def logout(self) -> None:
        self.send("C*logout*")
        self.__connection.close()

    def __str__(self) -> str:
        return f"XenoTable bound to {self.ip}:{self.port}"


class Communicator(Thread):
    communicators = {}
    current_port = 3000
    debug = False

    @staticmethod
    def my_ip() -> str:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip

    @staticmethod
    def local_sock() -> socket.socket:
        ip = Communicator.my_ip()
        sock = socket.socket()
        while True:
            try:
                sock.bind((ip, Communicator.current_port))
                break
            except OSError as e:
                Communicator.current_port += 1
                if Communicator.debug:
                    print(Communicator.current_port)
        return sock

    @staticmethod
    def create_sock(ip: str) -> socket.socket:
        sock = socket.socket()
        while True:
            try:
                sock.bind((ip, Communicator.current_port))
                break
            except OSError as e:
                Communicator.current_port += 1
                if Communicator.debug:
                    print(Communicator.current_port)
        return sock

    def __init__(self, sock: socket.socket, data: dict):
        super().__init__()
        self.sock = sock
        self.port = sock.getsockname()[1]
        self.ip = sock.getsockname()[0]
        self.start()
        self.data = data

    def recv(self, limit: int) -> list:
        command = ""
        num = 0
        while True:
            char = self.connection.recv(1).decode("UTF-8")
            if char == "*":
                num += 1
                if num == limit:
                    break
            command += char
        return command.split("*")

    def send(self, msg: str) -> None:
        self.connection.send(msg.encode("UTF-8"))

    def run(self) -> None:
        self.status = True
        try:
            if Communicator.debug:
                print("Listening at", self.port)
            self.sock.listen(16)
            self.connection, _ = self.sock.accept()
            Communicator(self.sock, self.data)
            self.send("true*")
            while self.status:
                command = self.recv(1)
                # Handle different commands here
                # ...
        finally:
            self.connection.close()
            self.status = False
