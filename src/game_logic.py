class DaraGame:
    def __init__(self):
        self.tabuleiro = [[0 for _ in range(6)] for _ in range(5)]
        self.fase = "posicionamento"
    
    def validar_movimento(self, l, c, jogador):
        # Lógica de regras do Dara
        pass