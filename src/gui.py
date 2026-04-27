import tkinter as tk
from tkinter import messagebox, scrolledtext
import sys
import os

class DaraGUI:
    def __init__(self, network_manager):
        self.net = network_manager
        self.my_id = self.net.proxy.register_player()
        
        self.root = tk.Tk()
        self.root.title(f"Dara Online - Player {self.my_id}")
        self.root.configure(bg="#F0F2F5") # Fundo cinza claro moderno
        
        # Paleta de Cores
        self.color_j1 = "#2196F3"    # Azul Material
        self.color_j1_light = "#BBDEFB"
        self.color_j2 = "#E91E63"    # Rosa/Magenta Material
        self.color_j2_light = "#F8BBD0"
        self.color_bg = "#FFFFFF"
        self.color_text = "#333333"

        self.main_container = tk.Frame(self.root, bg="#F0F2F5")
        self.main_container.pack(padx=20, pady=20, fill=tk.BOTH, expand=True)

        # --- ÁREA DA ESQUERDA ---
        self.left_area = tk.Frame(self.main_container, bg="#F0F2F5")
        self.left_area.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Frame do Jogo
        self.game_frame = tk.Frame(self.left_area, bg="#F0F2F5")
        self.game_frame.pack()

        # Badge de Status (Estilizado)
        self.status_container = tk.Frame(self.game_frame, bg="#FFFFFF", highlightbackground="#CCCCCC", highlightthickness=1)
        self.status_container.pack(pady=10, fill=tk.X)
        
        self.status_label = tk.Label(self.status_container, text="INICIANDO...", font=("Segoe UI", 12, "bold"), bg="#FFFFFF")
        self.status_label.pack(pady=8)

        # Grid de Botões
        self.grid_container = tk.Frame(self.game_frame, bg="#F0F2F5")
        self.grid_container.pack(pady=10)

        self.btn_grid = [[None for _ in range(6)] for _ in range(5)]
        for r in range(5):
            for c in range(6):
                btn = tk.Button(self.grid_container, width=8, height=3, 
                               font=("Arial", 10, "bold"), relief="flat",
                               cursor="hand2", command=lambda r=r, c=c: self._handle_click(r, c))
                btn.grid(row=r, column=c, padx=3, pady=3)
                self.btn_grid[r][c] = btn

        self.btn_desistir = tk.Button(self.game_frame, text="🏳️ Desistir", bg="#FF5252", fg="white", 
                                     font=("Segoe UI", 10, "bold"), relief="flat", padx=20,
                                     command=self._handle_surrender)
        self.btn_desistir.pack(pady=15)

        # Frame do Menu Pós-Jogo (Estilizado como Card)
        self.menu_frame = tk.Frame(self.left_area, bg="white", highlightbackground="#2196F3", highlightthickness=2)
        tk.Label(self.menu_frame, text="🏆 FIM DE JOGO", font=("Segoe UI", 18, "bold"), bg="white", fg="#333").pack(pady=20, padx=50)
        self.winner_info = tk.Label(self.menu_frame, text="", font=("Segoe UI", 12), bg="white")
        self.winner_info.pack(pady=10)
        
        menu_btn_style = {"font": ("Segoe UI", 10), "relief": "flat", "width": 25, "pady": 8}
        tk.Button(self.menu_frame, text="Visualizar Tabuleiro", bg="#E0E0E0", **menu_btn_style, command=self._show_game).pack(pady=5)
        tk.Button(self.menu_frame, text="Novo Jogo / Menu", bg="#4CAF50", fg="white", **menu_btn_style, command=self._restart).pack(pady=5)
        tk.Button(self.menu_frame, text="Sair do Dara", bg="#333333", fg="white", **menu_btn_style, command=sys.exit).pack(pady=5)

        # --- ÁREA DA DIREITA (CHAT) ---
        self.chat_frame = tk.Frame(self.main_container, bg="white", width=300, highlightbackground="#CCCCCC", highlightthickness=1)
        self.chat_frame.pack(side=tk.RIGHT, padx=(20, 0), fill=tk.Y)
        self.chat_frame.pack_propagate(False) # Mantém a largura fixa
        
        self.setup_chat()

        self.last_msg_count = 0
        self.game_over_active = False
        self.auto_refresh()

    def setup_chat(self):
        # Header do Chat
        header = tk.Frame(self.chat_frame, bg="#333")
        header.pack(fill=tk.X)
        tk.Label(header, text="CONVERSA", font=("Segoe UI", 9, "bold"), bg="#333", fg="white", pady=5).pack()

        # Display
        self.chat_display = scrolledtext.ScrolledText(self.chat_frame, font=("Segoe UI", 9), bg="white", state='disabled', relief="flat")
        self.chat_display.pack(pady=5, fill=tk.BOTH, expand=True)
        
        # Tags de Cor
        self.chat_display.tag_config("color_j1", foreground=self.color_j1, font=("Segoe UI", 9, "bold"))
        self.chat_display.tag_config("color_j2", foreground=self.color_j2, font=("Segoe UI", 9, "bold"))
        self.chat_display.tag_config("sys", foreground="#777777", font=("Segoe UI", 8, "italic"))

        # Input
        inp_f = tk.Frame(self.chat_frame, bg="white")
        inp_f.pack(fill=tk.X, padx=5, pady=10)
        
        self.chat_entry = tk.Entry(inp_f, font=("Segoe UI", 10), relief="solid", borderwidth=1)
        self.chat_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=3)
        self.chat_entry.bind("<Return>", lambda e: self._send_msg())
        
        tk.Button(inp_f, text="➤", font=("Arial", 12), bg=self.color_j1, fg="white", 
                  relief="flat", command=self._send_msg).pack(side=tk.RIGHT, padx=5)

    def _show_game(self):
        self.menu_frame.pack_forget()
        self.game_frame.pack()

    def _restart(self):
        self.root.destroy()
        os.system('python main.py')

    def _handle_click(self, r, c):
        res = self.net.proxy.make_move(r, c, self.my_id)
        if "ALERTA" in res: messagebox.showwarning("Dara - Regra", res)

    def _handle_surrender(self):
        if messagebox.askyesno("Desistir", "Sua dignidade está em jogo. Desistir mesmo?"):
            self.net.proxy.surrender(self.my_id)

    def _send_msg(self):
        msg = self.chat_entry.get()
        if msg:
            self.net.proxy.send_chat_message(self.my_id, msg)
            self.chat_entry.delete(0, tk.END)

    def auto_refresh(self):
        if not self.root.winfo_exists(): return
        try:
            board = self.net.proxy.get_board()
            status = self.net.proxy.get_status()
            turn = self.net.proxy.get_turn()
            msgs = self.net.proxy.get_chat_messages()

            # Atualiza Grid com cores suaves
            for r in range(5):
                for c in range(6):
                    val = board[r][c]
                    txt = "●" if val != 0 else "" # Peças em formato circular
                    color = self.color_j1 if val == 1 else self.color_j2 if val == 2 else "#E0E0E0"
                    bg_color = self.color_j1_light if val == 1 else self.color_j2_light if val == 2 else "#F9F9F9"
                    
                    self.btn_grid[r][c].config(text=txt, fg=color, bg=bg_color)

            # Status visual dinâmico
            self.status_label.config(text=status.upper())
            if turn == self.my_id:
                self.status_container.config(highlightbackground=self.color_j1 if self.my_id == 1 else self.color_j2)
            else:
                self.status_container.config(highlightbackground="#CCCCCC")

            # Fim de Jogo
            if "VENCEDOR" in status and not self.game_over_active:
                self.game_over_active = True
                self.game_frame.pack_forget()
                self.winner_info.config(text=status)
                self.menu_frame.pack(pady=40)

            # Mensagens
            if len(msgs) != self.last_msg_count:
                self.chat_display.config(state='normal')
                self.chat_display.delete(1.0, tk.END)
                for m in msgs:
                    tag = "color_j1" if m.startswith("J1") else "color_j2" if m.startswith("J2") else "sys"
                    self.chat_display.insert(tk.END, m + "\n", tag)
                self.chat_display.see(tk.END)
                self.chat_display.config(state='disabled')
                self.last_msg_count = len(msgs)
        except: pass
        self.root.after(500, self.auto_refresh)

    def start(self): self.root.mainloop()