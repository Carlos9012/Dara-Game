import tkinter as tk
import threading
from src.game_logic import DaraLogic
from src.network import NetworkManager
from src.gui import DaraGUI

class Launcher:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Dara Multiplayer")
        self.root.geometry("350x280")
        self.root.configure(bg="white")
        
        # Título
        tk.Label(self.root, text="DARA GAME", font=("Segoe UI", 20, "bold"), bg="white", fg="#333").pack(pady=20)
        
        # Porta
        tk.Label(self.root, text="Porta do Servidor", font=("Segoe UI", 9), bg="white", fg="#666").pack()
        self.port_entry = tk.Entry(self.root, justify='center', font=("Segoe UI", 10), relief="solid")
        self.port_entry.insert(0, "9090")
        self.port_entry.pack(pady=5, ipady=3)

        # Botões Estilizados
        btn_opts = {"font": ("Segoe UI", 10, "bold"), "relief": "flat", "width": 25, "pady": 10, "cursor": "hand2"}
        
        tk.Button(self.root, text="Hospedar Partida", bg="#4CAF50", fg="white", 
                  command=self.host, **btn_opts).pack(pady=10)
        
        tk.Button(self.root, text="Entrar em Partida", bg="#2196F3", fg="white", 
                  command=self.join, **btn_opts).pack(pady=5)

    def get_port(self):
        try: return int(self.port_entry.get())
        except: return 9090

    def host(self):
        p = self.get_port()
        threading.Thread(target=NetworkManager(DaraLogic(), p).start_server, daemon=True).start()
        self.root.after(500, self.join)

    def join(self):
        p = self.get_port()
        net = NetworkManager(port=p)
        if net.connect_to_server():
            self.root.withdraw()
            DaraGUI(net).start()
        else:
            from tkinter import messagebox
            messagebox.showerror("Erro", f"Servidor não encontrado em 'localhost:{p}'")

if __name__ == "__main__":
    Launcher().root.mainloop()