import tkinter as tk
from tkinter import ttk, messagebox
from tkinter.scrolledtext import ScrolledText
import socket

def listar_meus_ips():
    ips = ["127.0.0.1"]
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ips.append(s.getsockname()[0])
        s.close()
    except: pass
    return list(set(ips))

def validar_trio(tabuleiro, r, c, cor):
    if cor == 0: 
        return False
    
    # 1. Horizontal
    count_h = 1
    for i in range(c + 1, 6):
        if tabuleiro[r][i] == cor: 
            count_h += 1
        else: 
            break
    for i in range(c - 1, -1, -1):
        if tabuleiro[r][i] == cor: 
            count_h += 1
        else: 
            break
    if count_h >= 3: 
        return True

    # 2. Vertical
    count_v = 1
    for i in range(r + 1, 5):
        if tabuleiro[i][c] == cor: 
            count_v += 1
        else: 
            break
    for i in range(r - 1, -1, -1):
        if tabuleiro[i][c] == cor: 
            count_v += 1
        else: 
            break
            
    return count_v >= 3

# --- CLASSES DE INTERFACE ---

class MenuInicial(tk.Frame):
    def __init__(self, root, callback_conectar):
        """
        Refatorado para automatizar a escolha de cores:
        Host = Azul (Começa) | Client = Vermelho
        """
        self.frame = tk.Frame(root, padx=30, pady=30)
        self.frame.pack(expand=True)

        # Título do Jogo
        tk.Label(
            self.frame, 
            text="DARA MULTIPLAYER", 
            font=("Helvetica", 18, "bold"),
            fg="#333"
        ).pack(pady=(0, 20))

        # --- SEÇÃO DE CONEXÃO (IP) ---
        tk.Label(self.frame, text="Endereço IP do Host:", font=("Arial", 10)).pack()
        
        # Combobox para IPs frequentes (Facilita o teste local)
        self.combo_ip = ttk.Combobox(self.frame, values=["127.0.0.1", "localhost"], width=20)
        self.combo_ip.set("127.0.0.1")
        self.combo_ip.pack(pady=(5, 20))

        # --- BOTÕES DE AÇÃO ---
        # Botão para quem vai criar a sala (Sempre Azul)
        self.btn_host = tk.Button(
            self.frame, 
            text="CRIAR SALA", 
            bg="#FFFFFF",
            fg="#000000",
            font=("Arial", 10, "bold"),
            width=30,
            height=2,
            command=lambda: callback_conectar(self.combo_ip.get(), "azul", True)
        )
        self.btn_host.pack(pady=5)

        # Botão para quem vai entrar na sala (Sempre Vermelho)
        self.btn_client = tk.Button(
            self.frame, 
            text="ENTRAR EM SALA", 
            bg="#FFFFFF",
            fg="#000000",
            font=("Arial", 10, "bold"),
            width=30,
            height=2,
            command=lambda: callback_conectar(self.combo_ip.get(), "vermelho", False)
        )
        self.btn_client.pack(pady=5)

        # Nota Informativa
        tk.Label(
            self.frame, 
            text="* O Jogador Azul (Host) faz o primeiro movimento.", 
            font=("Arial", 8, "italic"), 
            fg="#666"
        ).pack(pady=(15, 0))

class TabuleiroGUI(tk.Frame):
    def __init__(self, master, minha_cor, ao_clicar, ao_desistir, ao_enviar_chat):
        super().__init__(master)
        self.ao_clicar = ao_clicar
        self.ao_desistir = ao_desistir
        self.ao_enviar_chat = ao_enviar_chat
        self.cores_map = {0: "white", "azul": "#3498db", "vermelho": "#e74c3c"}
        
        # --- Layout Principal ---
        self.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Container Esquerdo: Header + Tabuleiro
        self.f_esquerdo = tk.Frame(self)
        self.f_esquerdo.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        
        # Header (Status e Botão Desistir)
        self.header = tk.Frame(self.f_esquerdo)
        self.header.pack(fill='x', pady=(0, 10))
        
        self.label_status = tk.Label(self.header, text="Carregando...", font=('Arial', 11, 'bold'))
        self.label_status.pack(side="left")
        
        self.btn_desistir = tk.Button(self.header, text="🏳️ DESISTIR", bg="#f8d7da", fg="#721c24", 
                                     font=('Arial', 9, 'bold'), command=self.ao_desistir)
        self.btn_desistir.pack(side="right")

        # Grade do Tabuleiro
        self.grid_frame = tk.Frame(self.f_esquerdo, bg="#2c3e50", padx=5, pady=5)
        self.grid_frame.pack()
        
        self.botoes = []
        for r in range(5):
            linha = []
            for c in range(6):
                btn = tk.Button(self.grid_frame, width=9, height=4, relief="flat",
                               command=lambda r=r, c=c: self.ao_clicar(r, c))
                btn.grid(row=r, column=c, padx=2, pady=2)
                linha.append(btn)
            self.botoes.append(linha)
            
        # --- Container Direito: Chat ---
        self.f_chat = tk.LabelFrame(self, text="Chat da Partida", font=('Arial', 10, 'bold'))
        self.f_chat.grid(row=0, column=1, sticky="nsew")
        
        # Área de Texto Scrolled
        self.txt_mensagens = ScrolledText(self.f_chat, width=35, height=20, state="disabled", font=('Arial', 9))
        self.txt_mensagens.pack(padx=5, pady=5, fill="both", expand=True)
        
        # Container de Entrada
        self.f_entrada = tk.Frame(self.f_chat)
        self.f_entrada.pack(fill="x", padx=5, pady=(0, 5))
        
        self.entry_chat = tk.Entry(self.f_entrada, font=('Arial', 10))
        self.entry_chat.pack(side="left", fill="x", expand=True, padx=(0, 5))
        
        self.entry_chat.bind("<Return>", lambda event: self._enviar_local())
        
        tk.Button(self.f_entrada, text="Enviar", command=self._enviar_local).pack(side="right")

    def atualizar(self, matriz, restam, meu_turno, fase, sel=None):
        for r in range(5):
            for c in range(6):
                cor_hex = self.cores_map[matriz[r][c]]
                espessura = 4 if sel == (r, c) else 1
                borda = "black" if sel == (r, c) else "#bdc3c7"
                self.botoes[r][c].config(bg=cor_hex, highlightbackground=borda, highlightthickness=espessura)
        
        txt_turno = "SUA VEZ!" if meu_turno else "Aguarde o oponente..."
        cor_turno = "#27ae60" if meu_turno else "#7f8c8d"
        self.label_status.config(text=f"FASE: {fase.upper()} | Peças: {restam} | {txt_turno}", fg=cor_turno)

    def mostrar_tela_final(self, mensagem, ao_reiniciar, ao_menu, ao_sair):
        self.grid_frame.pack_forget()
        self.btn_desistir.pack_forget()
        
        self.frame_final = tk.Frame(self.f_esquerdo, bg="#f8f9fa", pady=40)
        self.frame_final.pack(fill="both", expand=True)

        tk.Label(self.frame_final, text=mensagem, font=('Arial', 14, 'bold'), 
                 bg="#f8f9fa", fg="#2c3e50", justify="center").pack(pady=20)

        estilo = {"width": 20, "height": 2, "font": ('Arial', 9, 'bold')}
        tk.Button(self.frame_final, text="REINICIAR PARTIDA", bg="#d1e7dd", command=ao_reiniciar, **estilo).pack(pady=5)
        tk.Button(self.frame_final, text="VOLTAR AO MENU", bg="#cfe2ff", command=ao_menu, **estilo).pack(pady=5)
        tk.Button(self.frame_final, text="FECHAR JOGO", bg="#f8d7da", command=ao_sair, **estilo).pack(pady=5)

    def adicionar_mensagem_chat(self, remetente, mensagem):
        cor_remetente = "#3498db" if remetente == "Você" else "#e74c3c"
        if remetente == "Sistema": cor_remetente = "#7f8c8d"
        
        self.txt_mensagens.config(state="normal")
        tag_nome = f"nome_{remetente}"
        self.txt_mensagens.insert(tk.END, f"{remetente}: ", tag_nome)
        self.txt_mensagens.tag_config(tag_nome, foreground=cor_remetente, font=('Arial', 9, 'bold'))
        self.txt_mensagens.insert(tk.END, f"{mensagem}\n")
        self.txt_mensagens.config(state="disabled")
        self.txt_mensagens.see(tk.END)

    def _enviar_local(self):
        msg = self.entry_chat.get().strip()
        if msg:
            self.entry_chat.delete(0, tk.END)
            self.adicionar_mensagem_chat("Você", msg)
            self.ao_enviar_chat(msg)