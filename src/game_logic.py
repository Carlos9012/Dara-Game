import Pyro5.api

@Pyro5.api.expose
class DaraLogic:
    def __init__(self):
        self.board = [[0 for _ in range(6)] for _ in range(5)]
        self.current_player = 1
        self.player_count = 0
        self.pieces_placed = {1: 0, 2: 0}
        self.max_pieces = 12
        self.selected_piece = {1: None, 2: None}
        self.waiting_capture = False 
        self.winner = None
        self.chat_messages = []

    def register_player(self):
        self.player_count += 1
        return self.player_count

    def surrender(self, player_id):
        if self.winner is None:
            self.winner = 2 if player_id == 1 else 1
            self.send_chat_message(0, f"O Jogador {player_id} desistiu!")

    def send_chat_message(self, player_id, msg):
        if msg.strip():
            prefix = f"J{player_id}" if player_id != 0 else "SISTEMA"
            self.chat_messages.append(f"{prefix}: {msg}")
            if len(self.chat_messages) > 15: self.chat_messages.pop(0)

    def get_chat_messages(self): return self.chat_messages
    def get_board(self): return self.board
    def get_turn(self): return self.current_player
    
    def check_trio(self, r, c, player_id):
        for dr, dc in [(0, 1), (1, 0)]:
            count = 1
            for d in [1, -1]:
                nr, nc = r + dr*d, c + dc*d
                while 0 <= nr < 5 and 0 <= nc < 6 and self.board[nr][nc] == player_id:
                    count += 1
                    nr, nc = nr + dr*d, nc + dc*d
            if count >= 3: return True
        return False

    def validar_posicionamento_seguro(self, r, c, player_id):
        if self.pieces_placed[1] < self.max_pieces or self.pieces_placed[2] < self.max_pieces:
            self.board[r][c] = player_id
            if self.check_trio(r, c, player_id):
                self.board[r][c] = 0 
                return False
            return True
        return True

    def make_move(self, r, c, player_id):
        if self.winner: return "Fim de jogo!"
        if player_id != self.current_player: return f"Aguarde o J{self.current_player}"

        if self.waiting_capture:
            opponent = 2 if player_id == 1 else 1
            if self.board[r][c] == opponent:
                self.board[r][c] = 0
                self.waiting_capture = False
                self._check_victory()
                self.current_player = opponent
                return "OK"
            return "ALERTA: Capture uma peça inimiga!"

        if self.pieces_placed[1] < self.max_pieces or self.pieces_placed[2] < self.max_pieces:
            if self.board[r][c] != 0: return "Ocupado!"
            if not self.validar_posicionamento_seguro(r, c, player_id):
                return "ALERTA: Proibido 3 em linha no posicionamento!"
            self.pieces_placed[player_id] += 1
            self.current_player = 2 if player_id == 1 else 1
            return "OK"

        if self.selected_piece[player_id] is None:
            if self.board[r][c] == player_id:
                self.selected_piece[player_id] = (r, c)
                return "Selecionado!"
        else:
            old_r, old_c = self.selected_piece[player_id]
            self.selected_piece[player_id] = None
            if abs(r - old_r) + abs(c - old_c) == 1 and self.board[r][c] == 0:
                self.board[old_r][old_c] = 0
                self.board[r][c] = player_id
                if self.check_trio(r, c, player_id):
                    self.waiting_capture = True
                    return "TRIO! Capture uma peça inimiga."
                self.current_player = 2 if player_id == 1 else 1
                return "OK"
        return "Ação inválida!"

    def _check_victory(self):
        p1 = sum(row.count(1) for row in self.board)
        p2 = sum(row.count(2) for row in self.board)
        if self.pieces_placed[1] == 12 and self.pieces_placed[2] == 12:
            if p1 <= 2: self.winner = 2
            elif p2 <= 2: self.winner = 1

    def get_status(self):
        if self.winner: return f"VENCEDOR: J{self.winner}!"
        if self.waiting_capture: return "FASE DE CAPTURA!"
        p1, p2 = self.pieces_placed[1], self.pieces_placed[2]
        if p1 < 12 or p2 < 12: return f"Drop: J1({p1}/12) J2({p2}/12)"
        return f"Vez do J{self.current_player}"