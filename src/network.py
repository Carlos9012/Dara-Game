import Pyro5.api

class NetworkManager:
    def __init__(self, logic_instance=None, port=9090):
        self.logic = logic_instance
        self.proxy = None
        self.port = int(port)

    def start_server(self):
        daemon = Pyro5.api.Daemon(host="localhost", port=self.port)
        uri = daemon.register(self.logic, "dara.game")
        print(f"Servidor ON na porta {self.port}")
        daemon.requestLoop()

    def connect_to_server(self):
        try:
            self.proxy = Pyro5.api.Proxy(f"PYRO:dara.game@localhost:{self.port}")
            self.proxy._pyroBind()
            return True
        except:
            return False