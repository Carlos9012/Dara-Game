import socket
import threading
import json

class DaraNetwork:
    def __init__(self, ip_alvo, porta=5000):
        self.ip = ip_alvo
        self.porta = porta
        self.socket = None
        self.socket_server = None # Para fechar o bind corretamente
        self.callback_receber = None
        self.conectado = False

    def iniciar_host(self):
        self.socket_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket_server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket_server.bind(('0.0.0.0', self.porta))
        self.socket_server.listen(1)
        # accept() é bloqueante, por isso rodamos na thread de bg_connect do main
        conn, _ = self.socket_server.accept()
        self.socket = conn
        self.conectado = True
        threading.Thread(target=self._ouvir, daemon=True).start()

    def conectar_ao_host(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.settimeout(10) # Timeout para não travar a thread pra sempre
        self.socket.connect((self.ip, self.porta))
        self.socket.settimeout(None) # Volta ao modo bloqueante para o recv
        self.conectado = True
        threading.Thread(target=self._ouvir, daemon=True).start()

    def enviar(self, dado):
        if self.socket and self.conectado:
            try:
                # Adicionamos um terminador \n para separar mensagens no buffer
                msg = json.dumps(dado) + "\n"
                self.socket.sendall(msg.encode('utf-8'))
            except Exception as e:
                print(f"Erro ao enviar: {e}")
                self.fechar()

    def _ouvir(self):
        buffer = ""
        while self.conectado:
            try:
                chunk = self.socket.recv(4096).decode('utf-8')
                if not chunk: break
                
                buffer += chunk
                # Lógica para tratar mensagens coladas (TCP fragmentation)
                while "\n" in buffer:
                    linha, buffer = buffer.split("\n", 1)
                    if linha.strip() and self.callback_receber:
                        self.callback_receber(json.loads(linha))
            except:
                break
        self.fechar()

    def fechar(self):
        """ Método essencial para evitar Memory Leaks e Portas Presas """
        self.conectado = False
        try:
            if self.socket: 
                self.socket.shutdown(socket.SHUT_RDWR)
                self.socket.close()
            if self.socket_server: 
                self.socket_server.close()
        except: pass
        self.socket = None
        self.socket_server = None