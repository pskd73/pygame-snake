import json
import threading


class SocketThread:
    def __init__(self, s, sid):
        self.socket = s
        self.sid = sid
        self.thread: threading.Thread = None
        self.running = False

    def start(self):
        self.thread = threading.Thread(target=self.listen)
        self.running = True
        self.thread.start()

    def send(self, message):
        print('sending', message)
        self.socket.send(json.dumps(message).encode())

    def close(self):
        self.running = False
        self.socket.close()

    @staticmethod
    def split_message(m: str):
        messages = []
        while True:
            try:
                i = m.index('}{')
            except ValueError:
                messages.append(m)
                return messages
            messages.append(m[:i+1])
            m = m[i+1:]

    def listen(self):
        print('listening to', self.socket)
        while self.running:
            messages = self.split_message(self.socket.recv(1024).decode())
            for message in messages:
                if message == '':
                    continue
                message = json.loads(message)
                print('received', message)
                if message['type']:
                    callback_attr_name = 'on_{}'.format(message['type'])
                    if hasattr(self, callback_attr_name):
                        self.__getattribute__(callback_attr_name)(message)
