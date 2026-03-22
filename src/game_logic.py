def validar_trio(tabuleiro, r, c, cor):
    """ Verifica se colocar uma peça em (r, c) forma uma linha de 3 ou mais """
    if cor == 0: return False
    
    count_h = 1
    for i in range(c + 1, 6):
        if tabuleiro[r][i] == cor: count_h += 1
        else: break
    for i in range(c - 1, -1, -1):
        if tabuleiro[r][i] == cor: count_h += 1
        else: break
    if count_h >= 3: return True

    count_v = 1
    for i in range(r + 1, 5):
        if tabuleiro[i][c] == cor: count_v += 1
        else: break
    for i in range(r - 1, -1, -1):
        if tabuleiro[i][c] == cor: count_v += 1
        else: break
            
    return count_v >= 3

class DaraLogic:
    def __init__(self):
        self.reset_logic()

    def reset_logic(self):
        self.tabuleiro = [[0 for _ in range(6)] for _ in range(5)]
        self.pecas_na_mao = 12
        self.totais_tabuleiro = 0
        self.fase = "posicionamento"
        self.esperando_captura = False
        self.pos_selecionada = None

    def contar_pecas(self):
        azul = sum(row.count("azul") for row in self.tabuleiro)
        vermelho = sum(row.count("vermelho") for row in self.tabuleiro)
        return azul, vermelho

    def validar_movimento(self, r_o, c_o, r_d, c_d):
        """ Regra: destino vazio e distância de apenas 1 casa (ortogonal) """
        dist = abs(r_d - r_o) + abs(c_d - c_o)
        return self.tabuleiro[r_d][c_d] == 0 and dist == 1