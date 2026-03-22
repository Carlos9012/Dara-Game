import tkinter as tk
from tkinter import messagebox
import threading
from src.gui import MenuInicial, TabuleiroGUI
from src.network import DaraNetwork
from src.game_logic import DaraLogic, validar_trio
import sys

def garantir_venv():
    executable_path = sys.executable.lower()
    esta_na_venv = ".venv" in executable_path
    
    if not esta_na_venv:
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror(
            "Erro de Ambiente", 
            f"Ambiente Virtual nao detectado!\n\n"
            f"Caminho atual: {sys.executable}\n"
            f"Por favor, use o 'run_game.bat'."
        )
        root.destroy()
        
        print("\n" + "!" * 50)
        print("ERRO CRITICO: AMBIENTE VIRTUAL NAO DETECTADO")
        print(f"Executavel sendo usado: {sys.executable}")
        print("!" * 50 + "\n")
        
        sys.exit(1)

class ControladorJogo:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Dara Multiplayer")
        self.root.geometry("+300+150")
        
        self.logic = DaraLogic()
        self.net = None
        self.minha_cor = ""
        self.meu_turno = False
        
        # Inicia direto no menu
        self.menu = MenuInicial(self.root, self.tentar_conexao)

    def tentar_conexao(self, ip, cor, sou_host):
        self.minha_cor = cor
        self.meu_turno = (cor == "azul")
        self.net = DaraNetwork(ip)
        
        def bg_connect():
            try:
                if sou_host: self.net.iniciar_host()
                else: self.net.conectar_ao_host()
                self.root.after(0, self.abrir_jogo)
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Erro", f"Falha: {e}"))
        
        threading.Thread(target=bg_connect, daemon=True).start()

    def abrir_jogo(self):
        for w in self.root.winfo_children(): w.destroy()
        
        self.gui = TabuleiroGUI(self.root, self.minha_cor, self.registrar_clique, 
                               self.confirmar_desistencia, self.enviar_mensagem_chat)
        
        self.gui.atualizar(self.logic.tabuleiro, self.logic.pecas_na_mao, self.meu_turno, self.logic.fase)
        self.gui.adicionar_mensagem_chat("Sistema", f"Conectado como {self.minha_cor.upper()}.")
        self.net.callback_receber = self.receber_dados

    def registrar_clique(self, r, c):
        if not self.meu_turno: return
        
        if self.logic.esperando_captura:
            self._executar_captura(r, c)
        elif self.logic.fase == "posicionamento":
            self._executar_posicionamento(r, c)
        else:
            self._executar_movimentacao(r, c)

    def _executar_posicionamento(self, r, c):
        if self.logic.tabuleiro[r][c] != 0 or self.logic.pecas_na_mao <= 0: return
        
        if validar_trio(self.logic.tabuleiro, r, c, self.minha_cor):
            messagebox.showwarning("Dara", "Não pode trios na fase de posicionamento!")
            return

        self.logic.tabuleiro[r][c] = self.minha_cor
        self.logic.pecas_na_mao -= 1
        self.logic.totais_tabuleiro += 1
        self.meu_turno = False
        
        if self.logic.totais_tabuleiro == 24: 
            self.logic.fase = "movimentacao"
            
        self.gui.atualizar(self.logic.tabuleiro, self.logic.pecas_na_mao, self.meu_turno, self.logic.fase)
        self.net.enviar({"tipo": "jogada", "r": r, "c": c, "cor": self.minha_cor, "fase": self.logic.fase})

    def _executar_movimentacao(self, r, c):
        if self.logic.pos_selecionada is None:
            if self.logic.tabuleiro[r][c] == self.minha_cor:
                self.logic.pos_selecionada = (r, c)
                self.gui.atualizar(self.logic.tabuleiro, 0, self.meu_turno, self.logic.fase, sel=(r,c))
            return
            
        r_o, c_o = self.logic.pos_selecionada
        if self.logic.validar_movimento(r_o, c_o, r, c):
            self.logic.tabuleiro[r_o][c_o] = 0
            self.logic.tabuleiro[r][c] = self.minha_cor
            self.logic.pos_selecionada = None
            
            mouro = validar_trio(self.logic.tabuleiro, r, c, self.minha_cor)
            self.net.enviar({"tipo": "movimento", "orig": (r_o, c_o), "dest": (r, c), "cor": self.minha_cor, "mouro": mouro})
            
            if mouro:
                self.logic.esperando_captura = True
                self.gui.atualizar(self.logic.tabuleiro, 0, self.meu_turno, "CAPTURA")
            else:
                self.meu_turno = False
                self.gui.atualizar(self.logic.tabuleiro, 0, self.meu_turno, self.logic.fase)
        else:
            self.logic.pos_selecionada = None
            self.gui.atualizar(self.logic.tabuleiro, 0, self.meu_turno, self.logic.fase)

    def _executar_captura(self, r, c):
        oponente = "vermelho" if self.minha_cor == "azul" else "azul"
        if self.logic.tabuleiro[r][c] == oponente:
            self.logic.tabuleiro[r][c] = 0
            self.logic.esperando_captura = False
            self.meu_turno = False 
            self.net.enviar({"tipo": "captura", "r": r, "c": c, "cor": self.minha_cor})
            self.gui.atualizar(self.logic.tabuleiro, 0, self.meu_turno, self.logic.fase)
            self._checar_vitoria()

    def _processar_dados(self, dados):
        t = dados["tipo"]
        if t == "chat":
            self.gui.adicionar_mensagem_chat("Oponente", dados["msg"])
        elif t == "desistencia":
            self._finalizar_partida("O OPONENTE DESISTIU!", False)
        elif t == "jogada":
            self.logic.tabuleiro[dados["r"]][dados["c"]] = dados["cor"]
            self.logic.totais_tabuleiro += 1
            if dados.get("fase") == "movimentacao": self.logic.fase = "movimentacao"
            self.meu_turno = True 
        elif t == "movimento":
            self.logic.tabuleiro[dados["orig"][0]][dados["orig"][1]] = 0
            self.logic.tabuleiro[dados["dest"][0]][dados["dest"][1]] = dados["cor"]
            self.meu_turno = not dados.get("mouro", False)
        elif t == "captura":
            self.logic.tabuleiro[dados["r"]][dados["c"]] = 0
            self.meu_turno = True
            self._checar_vitoria()
        
        self.gui.atualizar(self.logic.tabuleiro, self.logic.pecas_na_mao, self.meu_turno, self.logic.fase)

    def _checar_vitoria(self):
        if self.logic.fase != "movimentacao": return
        azul, vermelho = self.logic.contar_pecas()
        if azul <= 2: self._finalizar_partida("VERMELHO VENCEU!", True)
        elif vermelho <= 2: self._finalizar_partida("AZUL VENCEU!", False)

    def enviar_mensagem_chat(self, msg):
        if self.net: self.net.enviar({"tipo": "chat", "cor": self.minha_cor, "msg": msg})

    def receber_dados(self, dados):
        self.root.after(0, lambda: self._processar_dados(dados))

    def confirmar_desistencia(self):
        if messagebox.askyesno("Dara", "Deseja mesmo desistir?"):
            if self.net: self.net.enviar({"tipo": "desistencia"})
            self._finalizar_partida("VOCÊ DESISTIU!", True)

    def _finalizar_partida(self, mensagem, oponente_venceu):
        self.gui.mostrar_tela_final(mensagem, self._reiniciar, self._voltar_menu, self.root.quit)

    def _reiniciar(self):
        cor_salva = self.minha_cor
        self.logic.reset_logic()
        self.minha_cor = cor_salva
        self.meu_turno = (cor_salva == "azul")
        self.abrir_jogo()

    def _voltar_menu(self):
        if self.net:
            try: self.net.fechar()
            except: pass
            self.net = None
        for widget in self.root.winfo_children(): widget.destroy()
        self.logic.reset_logic()
        self.menu = MenuInicial(self.root, self.tentar_conexao)

if __name__ == "__main__":
    app = ControladorJogo()
    app.root.mainloop()