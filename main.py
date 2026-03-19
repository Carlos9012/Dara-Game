import tkinter as tk
from tkinter import messagebox
import threading
from src.gui import MenuInicial, TabuleiroGUI, validar_trio
from src.network import DaraNetwork

class ControladorJogo:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Dara Multiplayer")
        # Centraliza a janela principal
        self.root.geometry("+300+150")
        
        self.menu = MenuInicial(self.root, self.tentar_conexao)
        self.net = None
        self._reset_variaveis()

    def _reset_variaveis(self):
        self.tabuleiro = [[0 for _ in range(6)] for _ in range(5)]
        self.pecas_na_mao = 12
        self.totais_tabuleiro = 0
        self.fase = "posicionamento"
        self.esperando_captura = False
        self.pos_selecionada = None
        self.minha_cor = ""
        self.meu_turno = False

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
        # Remove o menu inicial
        for w in self.root.winfo_children(): w.destroy()
        
        # Cria a GUI passando os 5 argumentos necessários (incluindo o chat)
        self.gui = TabuleiroGUI(self.root, self.minha_cor, self.registrar_clique, 
                               self.confirmar_desistencia, self.enviar_mensagem_chat)
        
        self.gui.atualizar(self.tabuleiro, self.pecas_na_mao, self.meu_turno, self.fase)
        
        # Mensagem do sistema no chat
        self.gui.adicionar_mensagem_chat("Sistema", f"Conectado como {self.minha_cor.upper()}. Boa partida!")
        
        self.net.callback_receber = self.receber_dados

    def registrar_clique(self, r, c):
        if not self.meu_turno: return
        if self.esperando_captura: self._executar_captura(r, c)
        elif self.fase == "posicionamento": self._executar_posicionamento(r, c)
        else: self._executar_movimentacao(r, c)

    # --- Lógica do Chat ---
    def enviar_mensagem_chat(self, msg):
        """ Chamado pela GUI quando você envia uma mensagem """
        if self.net:
            # Envia pacote do tipo 'chat'
            self.net.enviar({"tipo": "chat", "cor": self.minha_cor, "msg": msg})

    # --- Lógica de Rede Integrada ---
    def receber_dados(self, dados):
        # Garante que a atualização da GUI ocorra na thread principal do Tkinter
        self.root.after(0, lambda: self._processar_dados(dados))

    def _processar_dados(self, dados):
        t = dados["tipo"]
        
        # Novo tratamento para mensagens de chat recebidas
        if t == "chat":
            remetente = "Oponente"
            self.gui.adicionar_mensagem_chat(remetente, dados["msg"])
            return # Interrompe o processamento, não é uma jogada

        # Tratamentos antigos (desistência, jogada, movimento, captura)
        elif t == "desistencia":
            self._finalizar_partida("O OPONENTE DESISTIU!\n🏆 VOCÊ VENCEU! 🏆", oponente_venceu=False)
            return

        elif t == "jogada":
            self.tabuleiro[dados["r"]][dados["c"]] = dados["cor"]
            self.totais_tabuleiro += 1
            if dados.get("fase") == "movimentacao": self.fase = "movimentacao"
            self.gui.adicionar_mensagem_chat("Sistema", f"{dados['cor'].upper()} posicionou em ({dados['r']},{dados['c']})")

        elif t == "movimento":
            self.tabuleiro[dados["orig"][0]][dados["orig"][1]] = 0
            self.tabuleiro[dados["dest"][0]][dados["dest"][1]] = dados["cor"]
            self.gui.adicionar_mensagem_chat("Sistema", f"{dados['cor'].upper()} moveu ({dados['orig'][0]},{dados['orig'][1]}) para ({dados['dest'][0]},{dados['dest'][1]})")

        elif t == "captura":
            self.tabuleiro[dados["r"]][dados["c"]] = 0
            self.gui.adicionar_mensagem_chat("Sistema", f"{dados['cor'].upper()} capturou a peça em ({dados['r']},{dados['c']})")
            self._checar_vitoria()
        
        # Se foi uma jogada, agora é o seu turno
        self.meu_turno = True
        self.gui.atualizar(self.tabuleiro, self.pecas_na_mao, self.meu_turno, self.fase)

    # --- Métodos Originais de Lógica de Jogo ---
    def _executar_posicionamento(self, r, c):
        if self.tabuleiro[r][c] != 0 or self.pecas_na_mao <= 0: return
        if validar_trio(self.tabuleiro, r, c, self.minha_cor):
            messagebox.showwarning("Dara", "Não pode trios na colocação!")
            return
        self.tabuleiro[r][c] = self.minha_cor
        self.pecas_na_mao -= 1
        self.totais_tabuleiro += 1
        self.meu_turno = False
        if self.totais_tabuleiro == 24: self.fase = "movimentacao"
        self.gui.atualizar(self.tabuleiro, self.pecas_na_mao, self.meu_turno, self.fase)
        self.net.enviar({"tipo": "jogada", "r": r, "c": c, "cor": self.minha_cor, "fase": self.fase})

    def _executar_movimentacao(self, r, c):
        if self.pos_selecionada is None:
            if self.tabuleiro[r][c] == self.minha_cor:
                self.pos_selecionada = (r, c)
                self.gui.atualizar(self.tabuleiro, 0, self.meu_turno, self.fase, sel=(r,c))
            return
        r_o, c_o = self.pos_selecionada
        dist = abs(r - r_o) + abs(c - c_o)
        if self.tabuleiro[r][c] == 0 and dist == 1:
            self.tabuleiro[r_o][c_o] = 0
            self.tabuleiro[r][c] = self.minha_cor
            self.pos_selecionada = None
            self.net.enviar({"tipo": "movimento", "orig": (r_o, c_o), "dest": (r, c), "cor": self.minha_cor})
            if validar_trio(self.tabuleiro, r, c, self.minha_cor):
                self.esperando_captura = True
                self.gui.atualizar(self.tabuleiro, 0, self.meu_turno, "CAPTURA")
                messagebox.showinfo("Dara", "TRIO! Capture uma peça inimiga.")
            else:
                self.meu_turno = False
                self.gui.atualizar(self.tabuleiro, 0, self.meu_turno, self.fase)
        else:
            self.pos_selecionada = None
            self.gui.atualizar(self.tabuleiro, 0, self.meu_turno, self.fase)

    def _executar_captura(self, r, c):
        oponente = "vermelho" if self.minha_cor == "azul" else "azul"
        if self.tabuleiro[r][c] == oponente:
            self.tabuleiro[r][c] = 0
            self.esperando_captura = False
            self.meu_turno = False
            self.gui.atualizar(self.tabuleiro, 0, self.meu_turno, self.fase)
            self.net.enviar({"tipo": "captura", "r": r, "c": c})
            self._checar_vitoria()
        else: messagebox.showwarning("Dara", "Selecione uma peça inimiga!")

    def _checar_vitoria(self):
        if self.fase != "movimentacao": return
        azul = sum(row.count("azul") for row in self.tabuleiro)
        vermelho = sum(row.count("vermelho") for row in self.tabuleiro)
        if azul <= 2: self._finalizar_partida("Azul ficou com 2 peças!\nVERMELHO VENCEU!", True)
        elif vermelho <= 2: self._finalizar_partida("Vermelho ficou com 2 peças!\nAZUL VENCEU!", False)

    # --- Finalização e Menu ---
    def confirmar_desistencia(self):
        if messagebox.askyesno("Dara", "Deseja mesmo desistir da partida?"):
            if self.net: self.net.enviar({"tipo": "desistencia"})
            self._finalizar_partida("VOCÊ DESISTIU!\nO oponente venceu.", oponente_venceu=True)

    def _finalizar_partida(self, mensagem, oponente_venceu):
        """ Substitui o tabuleiro pelo menu final integradamente """
        self.gui.mostrar_tela_final(
            mensagem, 
            ao_reiniciar=self._reiniciar, 
            ao_menu=self._voltar_menu, 
            ao_sair=self.root.quit
        )
        self.gui.adicionar_mensagem_chat("Sistema", "Fim de jogo. Chat continua ativo.")

    def _reiniciar(self):
        """ Reseta o estado mantendo o chat ativo """
        cor_salva = self.minha_cor
        self._reset_variaveis()
        self.minha_cor = cor_salva
        self.meu_turno = (cor_salva == "azul")
        self.abrir_jogo()
        self.gui.adicionar_mensagem_chat("Sistema", "Partida reiniciada!")

    def _voltar_menu(self):
        for w in self.root.winfo_children(): w.destroy()
        self.__init__()

if __name__ == "__main__":
    app = ControladorJogo()
    app.root.mainloop()