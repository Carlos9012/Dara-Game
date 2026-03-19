import tkinter as tk
from tkinter import ttk, messagebox
from tkinter.scrolledtext import ScrolledText
import socket

# --- FUNÇÕES GLOBAIS DE UTILIDADE ---

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
        if tabuleiro[i][c] == cor: # CORRIGIDO: Comparar com 'cor'
            count_v += 1
        else: 
            break
    for i in range(r - 1, -1, -1):
        if tabuleiro[i][c] == cor: # CORRIGIDO: Comparar com 'cor'
            count_v += 1
        else: 
            break
            
    return count_v >= 3

# --- CLASSES DE INTERFACE ---

class MenuInicial(tk.Frame):
    def __init__(self, master, ao_conectar):
        super().__init__(master)
        self.ao_conectar = ao_conectar
        self.pack(padx=30, pady=30)
        
        tk.Label(self, text="Dara Multiplayer", font=('Arial', 18, 'bold')).pack(pady=10)
        
        tk.Label(self, text="Seu IP local:").pack()
        self.combo_ip = ttk.Combobox(self, values=listar_meus_ips(), state="readonly")
        self.combo_ip.current(0)
        self.combo_ip.pack(fill='x', pady=5)
        
        self.cor_var = tk.StringVar(value="azul")
        f_cores = tk.LabelFrame(self, text="Sua Cor (Azul começa)")
        f_cores.pack(fill='x', pady=10, ipady=5)
        
        tk.Radiobutton(f_cores, text="Azul", variable=self.cor_var, value="azul", fg="blue", font=('Arial', 10, 'bold')).pack(side="left", padx=20)
        tk.Radiobutton(f_cores, text="Vermelho", variable=self.cor_var, value="vermelho", fg="red", font=('Arial', 10, 'bold')).pack(side="left", padx=20)
        
        tk.Button(self, text="CRIAR SALA (HOST)", bg="#d1e7dd", height=2, font=('Arial', 10, 'bold'),
                  command=lambda: self.ao_conectar(self.combo_ip.get(), self.cor_var.get(), True)).pack(fill='x', pady=2)
        
        tk.Button(self, text="ENTRAR EM SALA", bg="#cfe2ff", height=2, font=('Arial', 10, 'bold'),
                  command=lambda: self.ao_conectar(self.combo_ip.get(), self.cor_var.get(), False)).pack(fill='x', pady=2)

class TabuleiroGUI(tk.Frame):
    def __init__(self, master, minha_cor, ao_clicar, ao_desistir, ao_enviar_chat):
        super().__init__(master)
        self.ao_clicar = ao_clicar
        self.ao_desistir = ao_desistir
        self.ao_enviar_chat = ao_enviar_chat
        self.cores_map = {0: "white", "azul": "#3498db", "vermelho": "#e74c3c"}
        
        # --- Layout Principal (Usa Grid para separar Tabuleiro e Chat) ---
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
        
        # Área de Texto Scrolled (Rolagem Automática)
        self.txt_mensagens = ScrolledText(self.f_chat, width=35, height=20, state="disabled", font=('Arial', 9))
        self.txt_mensagens.pack(padx=5, pady=5, fill="both", expand=True)
        
        # Container de Entrada (Campo + Botão Enviar)
        self.f_entrada = tk.Frame(self.f_chat)
        self.f_entrada.pack(fill="x", padx=5, pady=(0, 5))
        
        self.entry_chat = tk.Entry(self.f_entrada, font=('Arial', 10))
        self.entry_chat.pack(side="left", fill="x", expand=True, padx=(0, 5))
        
        # Permite enviar com a tecla ENTER
        self.entry_chat.bind("<Return>", lambda event: self._enviar_local())
        
        tk.Button(self.f_entrada, text="Enviar", command=self._enviar_local).pack(side="right")

    def atualizar(self, matriz, restam, meu_turno, fase, sel=None):
        """ Atualiza visualmente o tabuleiro e os textos de status """
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
        """ Substitui o tabuleiro pelo menu final, mantendo o chat visível """
        self.grid_frame.pack_forget()
        self.btn_desistir.pack_forget()
        
        # Container para o menu final no lugar do tabuleiro
        self.frame_final = tk.Frame(self.f_esquerdo, bg="#f8f9fa", pady=40)
        self.frame_final.pack(fill="both", expand=True)

        tk.Label(self.frame_final, text=mensagem, font=('Arial', 14, 'bold'), 
                 bg="#f8f9fa", fg="#2c3e50", justify="center").pack(pady=20)

        estilo = {"width": 20, "height": 2, "font": ('Arial', 9, 'bold')}
        tk.Button(self.frame_final, text="REINICIAR PARTIDA", bg="#d1e7dd", command=ao_reiniciar, **estilo).pack(pady=5)
        tk.Button(self.frame_final, text="VOLTAR AO MENU", bg="#cfe2ff", command=ao_menu, **estilo).pack(pady=5)
        tk.Button(self.frame_final, text="FECHAR JOGO", bg="#f8d7da", command=ao_sair, **estilo).pack(pady=5)

    def adicionar_mensagem_chat(self, remetente, mensagem):
        """ Adiciona uma mensagem na área de texto e rola para o fim """
        cor_remetente = "#3498db" if remetente == "Você" else "#e74c3c"
        if remetente == "Sistema": cor_remetente = "#7f8c8d"
        
        self.txt_mensagens.config(state="normal")
        
        # Adiciona o nome do remetente com cor
        tag_nome = f"nome_{remetente}"
        self.txt_mensagens.insert(tk.END, f"{remetente}: ", tag_nome)
        self.txt_mensagens.tag_config(tag_nome, foreground=cor_remetente, font=('Arial', 9, 'bold'))
        
        # Adiciona a mensagem
        self.txt_mensagens.insert(tk.END, f"{mensagem}\n")
        self.txt_mensagens.config(state="disabled")
        
        # Rola para o fim
        self.txt_mensagens.see(tk.END)

    def _enviar_local(self):
        """ Pega o texto da entrada, limpa o campo e chama o callback do main """
        msg = self.entry_chat.get().strip()
        if msg:
            self.entry_chat.delete(0, tk.END)
            # Adiciona localmente como "Você"
            self.adicionar_mensagem_chat("Você", msg)
            # Envia para a rede
            self.ao_enviar_chat(msg)