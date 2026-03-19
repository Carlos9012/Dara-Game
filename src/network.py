import socket
import threading
import json

class DaraNetwork:
    def __init__(self, ip_alvo, porta=5000):
        self.ip = ip_alvo
        self.porta = porta
        self.socket = None
        self.callback_receber = None

    def iniciar_host(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(('0.0.0.0', self.porta))
        s.listen(1)
        self.socket, _ = s.accept()
        threading.Thread(target=self._ouvir, daemon=True).start()

    def conectar_ao_host(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((self.ip, self.porta))
        threading.Thread(target=self._ouvir, daemon=True).start()

    def enviar(self, dado):
        if self.socket:
            try:
                # Envia o JSON como string codificada em UTF-8
                self.socket.send(json.dumps(dado).encode('utf-8'))
            except: pass

    def _ouvir(self):
        while True:
            try:
                # Aumentei o buffer para 4096 para mensagens de chat mais longas
                msg = self.socket.recv(4096).decode('utf-8')
                if not msg: break
                if self.callback_receber:
                    self.callback_receber(json.loads(msg))
            except: break