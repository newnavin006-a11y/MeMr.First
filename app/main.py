import sys
import time
import os

import pygame
import random
PIECES_DIR = os.path.join('..', 'assets', 'pieces')
import chess
import chess.pgn


class ChessGUI:
    def __init__(self, singleplayer=False, time_control_enabled=False, time_seconds=300, ai_depth=2):
        pygame.init()
        self.size = 640
        self.screen = pygame.display.set_mode((self.size, self.size + 60))
        pygame.display.set_caption('PyChess')
        self.clock = pygame.time.Clock()
        self.square_size = self.size // 8

        self.board = chess.Board()
        self.selected = None
        self.legal_moves = []
        self.singleplayer = singleplayer
        self.ai_depth = ai_depth

        self.time_control_enabled = time_control_enabled
        self.time_seconds = time_seconds
        self.clocks = {chess.WHITE: time_seconds, chess.BLACK: time_seconds}
        self.last_move_time = time.time()

        self.piece_images = self.generate_piece_images()
        self.running = True
        self.pending_ai_move = None
        self.ai_move_ready_time = None

    def draw(self):
        colors = [(240, 217, 181), (181, 136, 99)]
        for r in range(8):
            for c in range(8):
                color = colors[(r + c) % 2]
                rect = pygame.Rect(c * self.square_size, r * self.square_size, self.square_size, self.square_size)
                pygame.draw.rect(self.screen, color, rect)

        # pieces
        for sq in chess.SQUARES:
            piece = self.board.piece_at(sq)
            if piece:
                row = 7 - chess.square_rank(sq)
                col = chess.square_file(sq)
                image = self.piece_images.get((piece.piece_type, piece.color))
                if image:
                    x = col * self.square_size + (self.square_size - image.get_width()) // 2
                    y = row * self.square_size + (self.square_size - image.get_height()) // 2
                    self.screen.blit(image, (x, y))

        # highlight selected and moves
        if self.selected is not None:
            srow = 7 - chess.square_rank(self.selected)
            scol = chess.square_file(self.selected)
            sel_rect = pygame.Rect(scol * self.square_size, srow * self.square_size, self.square_size, self.square_size)
            pygame.draw.rect(self.screen, (0, 255, 0), sel_rect, 3)
            for m in self.legal_moves:
                if m.from_square == self.selected:
                    drow = 7 - chess.square_rank(m.to_square)
                    dcol = chess.square_file(m.to_square)
                    center = (dcol * self.square_size + self.square_size // 2, drow * self.square_size + self.square_size // 2)
                    pygame.draw.circle(self.screen, (0, 0, 0), center, 8)

        # clocks
        pygame.draw.rect(self.screen, (30, 30, 30), (0, self.size, self.size, 60))
        small = pygame.font.SysFont(None, 28)
        wtime = self.clocks.get(chess.WHITE, 0)
        btime = self.clocks.get(chess.BLACK, 0)
        wtxt = small.render(f'White: {int(wtime)}s', True, (255, 255, 255))
        btxt = small.render(f'Black: {int(btime)}s', True, (255, 255, 255))
        self.screen.blit(wtxt, (10, self.size + 10))
        self.screen.blit(btxt, (10, self.size + 30))

        # hints
        hint = small.render('S:Save PGN  L:Load PGN  U:Undo', True, (200, 200, 200))
        self.screen.blit(hint, (220, self.size + 20))

    def coord_to_square(self, x, y):
        col = x // self.square_size
        row = y // self.square_size
        if 0 <= col < 8 and 0 <= row < 8:
            sq = chess.square(col, 7 - row)
            return sq
        return None

    def generate_piece_images(self):
        images = {}
        mapping = {
            chess.PAWN: 'P',
            chess.KNIGHT: 'N',
            chess.BISHOP: 'B',
            chess.ROOK: 'R',
            chess.QUEEN: 'Q',
            chess.KING: 'K',
        }
        for piece_type, code in mapping.items():
            for color in [chess.WHITE, chess.BLACK]:
                color_prefix = 'w' if color == chess.WHITE else 'b'
                fname = os.path.join(PIECES_DIR, f'{color_prefix}{code}.png')
                if os.path.exists(fname):
                    try:
                        img = pygame.image.load(fname).convert_alpha()
                        img = pygame.transform.smoothscale(img, (self.square_size, self.square_size))
                        images[(piece_type, color)] = img
                        continue
                    except Exception:
                        pass
                surf = pygame.Surface((self.square_size, self.square_size), pygame.SRCALPHA)
                self.draw_piece_icon(surf, piece_type, color)
                images[(piece_type, color)] = surf
        return images

    def draw_piece_icon(self, surf, piece_type, color):
        light = (240, 240, 240)
        dark = (30, 30, 30)
        fill = light if color == chess.WHITE else dark
        outline = dark if color == chess.WHITE else light
        w, h = surf.get_size()
        base_rect = pygame.Rect(w * 0.2, h * 0.6, w * 0.6, h * 0.2)
        pygame.draw.ellipse(surf, fill, base_rect)
        pygame.draw.ellipse(surf, outline, base_rect, 2)
        body = pygame.Rect(w * 0.32, h * 0.35, w * 0.36, h * 0.35)
        pygame.draw.rect(surf, fill, body)
        pygame.draw.rect(surf, outline, body, 2)
        if piece_type == chess.PAWN:
            pygame.draw.circle(surf, fill, (w // 2, int(h * 0.25)), int(w * 0.14))
            pygame.draw.circle(surf, outline, (w // 2, int(h * 0.25)), int(w * 0.14), 2)
        elif piece_type == chess.KNIGHT:
            points = [
                (w * 0.3, h * 0.55),
                (w * 0.38, h * 0.3),
                (w * 0.52, h * 0.22),
                (w * 0.68, h * 0.34),
                (w * 0.6, h * 0.52),
                (w * 0.42, h * 0.52),
            ]
            pygame.draw.polygon(surf, fill, points)
            pygame.draw.lines(surf, outline, False, points, 2)
            pygame.draw.circle(surf, outline, (int(w * 0.56), int(h * 0.36)), int(w * 0.04))
        elif piece_type == chess.BISHOP:
            pygame.draw.ellipse(surf, fill, (w * 0.33, h * 0.2, w * 0.34, h * 0.25))
            pygame.draw.ellipse(surf, outline, (w * 0.33, h * 0.2, w * 0.34, h * 0.25), 2)
            pygame.draw.line(surf, outline, (w * 0.37, h * 0.27), (w * 0.63, h * 0.33), 3)
        elif piece_type == chess.ROOK:
            top = pygame.Rect(w * 0.28, h * 0.18, w * 0.44, h * 0.14)
            pygame.draw.rect(surf, fill, top)
            pygame.draw.rect(surf, outline, top, 2)
            for i in range(4):
                rect = pygame.Rect(w * (0.28 + 0.1 * i), h * 0.18, w * 0.08, h * 0.08)
                pygame.draw.rect(surf, fill, rect)
                pygame.draw.rect(surf, outline, rect, 2)
        elif piece_type == chess.QUEEN:
            crown = [(w * 0.28, h * 0.3), (w * 0.37, h * 0.16), (w * 0.5, h * 0.26), (w * 0.63, h * 0.16), (w * 0.72, h * 0.3)]
            pygame.draw.polygon(surf, fill, crown)
            pygame.draw.lines(surf, outline, False, crown, 2)
            pygame.draw.circle(surf, outline, (int(w * 0.37), int(h * 0.16)), int(w * 0.03))
            pygame.draw.circle(surf, outline, (int(w * 0.5), int(h * 0.26)), int(w * 0.03))
            pygame.draw.circle(surf, outline, (int(w * 0.63), int(h * 0.16)), int(w * 0.03))
        elif piece_type == chess.KING:
            crown = [(w * 0.28, h * 0.28), (w * 0.4, h * 0.16), (w * 0.5, h * 0.24), (w * 0.6, h * 0.16), (w * 0.72, h * 0.28)]
            pygame.draw.polygon(surf, fill, crown)
            pygame.draw.lines(surf, outline, False, crown, 2)
            pygame.draw.rect(surf, fill, (w * 0.47, h * 0.15, w * 0.08, h * 0.18))
            pygame.draw.rect(surf, outline, (w * 0.47, h * 0.15, w * 0.08, h * 0.18), 2)
            pygame.draw.line(surf, outline, (w * 0.45, h * 0.16), (w * 0.55, h * 0.16), 3)
            pygame.draw.line(surf, outline, (w * 0.5, h * 0.13), (w * 0.5, h * 0.19), 3)
        pygame.draw.rect(surf, outline, (w * 0.2, h * 0.6, w * 0.6, h * 0.2), 2)

    def ai_move(self):
        # compute move and schedule it after a delay to simulate thinking
        is_maximising = self.board.turn == chess.WHITE
        move = self.alpha_beta_root(self.ai_depth, self.board, is_maximising)
        if move:
            delay = 0.6 + self.ai_depth * 0.8 + random.uniform(-0.5, 1.2)
            delay = max(0.3, delay)
            self.pending_ai_move = move
            self.ai_move_ready_time = time.time() + delay

    def alpha_beta_root(self, depth, board, is_maximising):
        best_move = None
        alpha = -99999
        beta = 99999
        if is_maximising:
            best_value = -99999
            for move in self.order_moves(board):
                board.push(move)
                val = self.alpha_beta(depth - 1, board, alpha, beta, not is_maximising)
                board.pop()
                if val > best_value:
                    best_value = val
                    best_move = move
                alpha = max(alpha, val)
                if beta <= alpha:
                    break
        else:
            best_value = 99999
            for move in self.order_moves(board):
                board.push(move)
                val = self.alpha_beta(depth - 1, board, alpha, beta, not is_maximising)
                board.pop()
                if val < best_value:
                    best_value = val
                    best_move = move
                beta = min(beta, val)
                if beta <= alpha:
                    break
        return best_move

    def alpha_beta(self, depth, board, alpha, beta, is_max):
        if depth == 0 or board.is_game_over():
            return self.evaluate(board)
        if is_max:
            value = -99999
            for move in self.order_moves(board):
                board.push(move)
                value = max(value, self.alpha_beta(depth - 1, board, alpha, beta, False))
                board.pop()
                alpha = max(alpha, value)
                if alpha >= beta:
                    break
            return value
        else:
            value = 99999
            for move in self.order_moves(board):
                board.push(move)
                value = min(value, self.alpha_beta(depth - 1, board, alpha, beta, True))
                board.pop()
                beta = min(beta, value)
                if alpha >= beta:
                    break
            return value

    def move_order_score(self, board, move):
        score = 0
        if board.is_capture(move):
            target = board.piece_at(move.to_square)
            if target:
                score += 1000 * self.evaluate_capture(target.piece_type)
        if move.promotion:
            score += 900
        return score

    def evaluate_capture(self, piece_type):
        values = {
            chess.PAWN: 1,
            chess.KNIGHT: 3,
            chess.BISHOP: 3,
            chess.ROOK: 5,
            chess.QUEEN: 9,
            chess.KING: 1000,
        }
        return values.get(piece_type, 0)

    def order_moves(self, board):
        moves = list(board.legal_moves)
        moves.sort(key=lambda m: self.move_order_score(board, m), reverse=True)
        return moves

    def evaluate(self, board):
        if board.is_checkmate():
            return 99999 if board.turn == chess.BLACK else -99999
        if board.is_stalemate() or board.is_insufficient_material() or board.can_claim_draw():
            return 0
        vals = {chess.PAWN: 100, chess.KNIGHT: 320, chess.BISHOP: 330, chess.ROOK: 500, chess.QUEEN: 900, chess.KING: 20000}
        score = 0
        for sq in chess.SQUARES:
            p = board.piece_at(sq)
            if p:
                v = vals.get(p.piece_type, 0)
                score += v if p.color == chess.WHITE else -v
        return score

    def update_clock(self):
        if not self.time_control_enabled:
            return
        now = time.time()
        elapsed = now - self.last_move_time
        turn = self.board.turn
        self.clocks[turn] = max(0, self.clocks[turn] - elapsed)
        self.last_move_time = now

    def run(self):
        while self.running:
            self.clock.tick(30)
            self.update_clock()

            if self.time_control_enabled:
                if self.clocks[chess.WHITE] <= 0 or self.clocks[chess.BLACK] <= 0:
                    winner = 'Black' if self.clocks[chess.WHITE] <= 0 else 'White'
                    print(f'Time over. {winner} wins')
                    self.running = False
                    break

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    x, y = event.pos
                    if y > self.size:
                        continue
                    sq = self.coord_to_square(x, y)
                    if sq is None:
                        continue
                    piece = self.board.piece_at(sq)
                    if self.selected is None:
                        if piece and piece.color == self.board.turn:
                            self.selected = sq
                            self.legal_moves = [m for m in self.board.legal_moves if m.from_square == sq]
                    else:
                        move = None
                        for m in self.legal_moves:
                            if m.to_square == sq:
                                move = m
                                break
                        if move:
                            self.board.push(move)
                            self.last_move_time = time.time()
                        self.selected = None
                        self.legal_moves = []
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_s:
                        ts = time.strftime('%Y%m%d_%H%M%S')
                        os.makedirs('saved_games', exist_ok=True)
                        fname = os.path.join('saved_games', f'game_{ts}.pgn')
                        try:
                            game = chess.pgn.Game.from_board(self.board)
                            with open(fname, 'w', encoding='utf-8') as f:
                                exporter = chess.pgn.FileExporter(f)
                                game.accept(exporter)
                            print('Saved PGN to', fname)
                        except Exception as e:
                            print('Failed to save PGN:', e)
                    elif event.key == pygame.K_l:
                        sgdir = 'saved_games'
                        fname = None
                        if os.path.isdir(sgdir):
                            files = [os.path.join(sgdir, f) for f in os.listdir(sgdir) if f.endswith('.pgn')]
                            files.sort()
                            if files:
                                fname = files[-1]
                        if fname and os.path.exists(fname):
                            try:
                                with open(fname, 'r', encoding='utf-8') as f:
                                    game = chess.pgn.read_game(f)
                                board = game.board()
                                for mv in game.mainline_moves():
                                    board.push(mv)
                                self.board = board
                                self.selected = None
                                self.legal_moves = []
                                print('Loaded PGN from', fname)
                            except Exception as e:
                                print('Failed to load PGN:', e)
                        else:
                            print('No PGN file found in saved_games')
                    elif event.key == pygame.K_u:
                        if len(self.board.move_stack) > 0:
                            self.board.pop()

            # AI turn (non-blocking: compute then wait, then push)
            if self.singleplayer and not self.board.is_game_over():
                ai_turn = (self.board.turn == chess.BLACK)
                if ai_turn:
                    if self.pending_ai_move is None:
                        self.ai_move()
                    else:
                        if time.time() >= self.ai_move_ready_time:
                            try:
                                self.board.push(self.pending_ai_move)
                            except Exception:
                                pass
                            self.pending_ai_move = None
                            self.ai_move_ready_time = None
                            self.last_move_time = time.time()

            if self.board.is_checkmate():
                print('Checkmate!')
                self.running = False

            self.screen.fill((0, 0, 0))
            self.draw()
            pygame.display.flip()

        pygame.quit()


def show_start_menu():
    pygame.init()
    screen = pygame.display.set_mode((640, 700))
    pygame.display.set_caption('PyChess Setup')
    clock = pygame.time.Clock()
    font = pygame.font.SysFont(None, 28)
    large_font = pygame.font.SysFont(None, 40)

    singleplayer = True
    time_control_enabled = False
    seconds = 300
    difficulty = 1
    seconds_options = [30, 60, 180, 300, 600]
    running = True

    while running:
        # prepare button rects so clicks can be detected before rendering
        seconds_rects = []
        diff_rects = []
        single_rect = pygame.Rect(220, 74, 120, 30)
        time_rect = pygame.Rect(220, 114, 120, 30)
        start_rect = pygame.Rect(220, 240, 120, 40)
        for i, s in enumerate(seconds_options):
            r = pygame.Rect(220 + i * 80, 154, 70, 30)
            seconds_rects.append(r)
        for i in range(3):
            r = pygame.Rect(220 + i * 80, 194, 70, 30)
            diff_rects.append(r)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit(0)
            elif event.type == pygame.MOUSEBUTTONDOWN:
                x, y = event.pos
                if single_rect.collidepoint(x, y):
                    singleplayer = not singleplayer
                elif time_rect.collidepoint(x, y):
                    time_control_enabled = not time_control_enabled
                elif start_rect.collidepoint(x, y):
                    running = False
                else:
                    for idx, rect in enumerate(seconds_rects):
                        if rect.collidepoint(x, y):
                            seconds = seconds_options[idx]
                    for idx, rect in enumerate(diff_rects):
                        if rect.collidepoint(x, y):
                            difficulty = idx + 1

        screen.fill((18, 24, 47))
        title = large_font.render('PyChess Settings', True, (255, 255, 255))
        screen.blit(title, (20, 20))

        single_text = font.render(f'Single-player: {"Yes" if singleplayer else "No"}', True, (255, 255, 255))
        screen.blit(single_text, (20, 80))
        pygame.draw.rect(screen, (70, 130, 180) if singleplayer else (80, 80, 80), single_rect)
        single_lbl = font.render('Toggle', True, (255, 255, 255))
        screen.blit(single_lbl, (single_rect.x + 10, single_rect.y + 5))

        time_text = font.render(f'Time control: {"On" if time_control_enabled else "Off"}', True, (255, 255, 255))
        screen.blit(time_text, (20, 120))
        pygame.draw.rect(screen, (70, 130, 180) if time_control_enabled else (80, 80, 80), time_rect)
        time_lbl = font.render('Toggle', True, (255, 255, 255))
        screen.blit(time_lbl, (time_rect.x + 10, time_rect.y + 5))

        sec_text = font.render('Seconds per side:', True, (255, 255, 255))
        screen.blit(sec_text, (20, 160))
        for i, r in enumerate(seconds_rects):
            s = seconds_options[i]
            pygame.draw.rect(screen, (70, 130, 180) if seconds == s else (120, 120, 120), r)
            s_lbl = font.render(str(s), True, (255, 255, 255))
            screen.blit(s_lbl, (r.x + 10, r.y + 5))

        diff_text = font.render('Difficulty:', True, (255, 255, 255))
        screen.blit(diff_text, (20, 200))
        for i, r in enumerate(diff_rects):
            pygame.draw.rect(screen, (70, 130, 180) if difficulty == i + 1 else (120, 120, 120), r)
            d_lbl = font.render(str(i + 1), True, (255, 255, 255))
            screen.blit(d_lbl, (r.x + 10, r.y + 5))

        pygame.draw.rect(screen, (34, 177, 76), start_rect)
        start_lbl = font.render('Start Game', True, (255, 255, 255))
        screen.blit(start_lbl, (start_rect.x + 10, start_rect.y + 10))

        pygame.display.flip()
        clock.tick(30)

    pygame.display.quit()
    return singleplayer, time_control_enabled, seconds, difficulty


if __name__ == '__main__':
    sp, tc, secs, depth = show_start_menu()
    gui = ChessGUI(singleplayer=sp, time_control_enabled=tc, time_seconds=secs, ai_depth=depth)
    gui.run()
