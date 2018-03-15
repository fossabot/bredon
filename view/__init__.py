from model import *
import tkinter as tk
import time

TILE_SIZE = 40
SQUARE_SIZE = 75
ANIM_STEPS = 30


class ViewSquare:
    def __init__(self, master, i, j, width=SQUARE_SIZE, height=SQUARE_SIZE):
        self.width = width
        self.height = height
        self.master = master
        self.i, self.j = i, j
        self.ix, self.jy = self.i * SQUARE_SIZE + 2, self.j * SQUARE_SIZE + 2
        self.tags = str(i) + "." + str(j)
        self.ids = []

    def _render(self, tile, idx, offset_x=0.0, offset_y=0.0):
        n, s, o, d = self._calc_nsod(idx)

        x1, y1 = offset_x + self.ix + s - n, offset_y + self.jy + s - n - o + d
        x2, y2 = offset_x + self.ix + s + n, offset_y + self.jy + s + n - o + d
        if tile.stone == FLAT:
            return self.master.canvas.create_rectangle(x1, y1, x2, y2, fill=tile.color, tags=(self.tags, idx))
        elif tile.stone == STAND:
            return self.master.canvas.create_polygon(x1 + n * 1.5, y1,
                                                     x2, y1 + n * 0.5,
                                                     x1 + n * 0.5, y2,
                                                     x1, y1 + n * 1.5, fill=tile.color, outline='black', tags=(self.tags, idx))
        else:
            return self.create_circle(*self.find_center(idx, offset_x, offset_y),  s / 2, fill=tile.color, tags=(self.tags, idx))

    def find_center(self, idx, offset_x=0.0, offset_y=0.0):
        n, s, o, d = self._calc_nsod(idx)
        return offset_x + self.ix + s, offset_y + self.jy + s - o + d

    def _calc_nsod(self, idx):
        return TILE_SIZE / 2, SQUARE_SIZE / 2, 3 * idx, 5

    def render(self, active=False):
        self.master.canvas.create_rectangle(self.ix, self.jy, self.ix + SQUARE_SIZE, self.jy + SQUARE_SIZE,
                                            fill="green" if active else "white")
        self.ids = [self._render(tile, idx) for idx, tile in enumerate(self.get_tiles(self.master.board), start=1)]

    def create_circle(self, x, y, r, **kwargs):
        return self.master.canvas.create_oval(x - r, y - r, x + r, y + r, **kwargs)

    def get_tiles(self, board):
        return board.board[self.i][self.j].tiles

    def s(self, b):
        return self.tags + " " + str(self.get_tiles(b))


class ViewBoard(tk.Frame):
    def __init__(self, master, board: Board):
        self.board = board
        self.size = board.size
        self.squares = []

        tk.Frame.__init__(self, master, width=self.size * SQUARE_SIZE, height=self.size * SQUARE_SIZE)
        self.canvas = tk.Canvas(self, width=self.size * SQUARE_SIZE, height=self.size * SQUARE_SIZE)
        self.pack()
        self.canvas.pack()
        self._init_gui()
        self.actives = [False for _ in range(self.size ** 2)]
        self.move = None

    def _init_gui(self):
        for i in range(self.size):
            for j in range(self.size):
                self.squares.append(ViewSquare(self, i, j))

    def execute(self, move, player, old_board):
        new_board = self.board.copy()
        new_board.force_str(move, player)
        idx = 0
        for rn, ro in zip(new_board.board, old_board.board):
            for nsq, sq in zip(rn, ro):
                if str(nsq) != str(sq):
                    self.actives[idx] = True
                idx += 1
        self.render()
        self.move = move, old_board

    def animate(self, move, old_board):
        print("animating", move)
        m = str_to_move(move)
        sq = int(cols.index(m.col)), int(m.row) - 1
        moves = m.moves if m.moves else [m.total]
        print("found", sq, moves)
        t = m.total
        if len(moves) == 1:
            self._animate(sq, m.direction, 0, moves[0], old_board, slice(-t, None))
        else:
            for i, move in enumerate(moves):
                stop = -(t-move)
                if stop == 0:
                    stop = None
                self._animate(sq, m.direction, i, move, old_board, slice(-t, stop))
                t -= move

    def _animate(self, sq, direction, i, n, old_board, idxs):
        print("\t_animating", sq, direction, i, n, idxs)

        vis = self.get_square(sq)
        tiles = vis.get_tiles(old_board)[idxs]
        ids = vis.ids[idxs]

        nvis = Square(*sq).tru_next(direction, self.size)
        for j in range(i):
            nvis = Square(*nvis).tru_next(direction, self.size)
        nts = self.get_square(nvis).get_tiles(old_board)

        step = SQUARE_SIZE / ANIM_STEPS * (i + 1)
        if direction == UP:
            step -= (3 * len(nts)) / ANIM_STEPS
            xi, yi = step, 0
        elif direction == DOWN:
            xi, yi = -step, 0
        elif direction == RIGHT:
            xi, yi = 0, -step
        elif direction == LEFT:
            xi, yi = 0, step

        print("\tstates:")
        print("\t\tvis", vis.s(old_board))
        for name, var in zip(("tiles", "ids", "nvis", "nts", "step", "xi", "yi"),
                             (tiles, ids, nvis, nts, step, xi, yi)):
            print("\t\t", name, var)

        for k in range(2, ANIM_STEPS):
            for _id in ids:
                self.canvas.delete(_id)
            ids = [vis._render(tile, _idx, -(yi * k), (xi * k) - ((_idx - 1) * 3) * (k / ANIM_STEPS)) for _idx, tile in enumerate(tiles, start=1)]
            self.update()

    def get_square(self, sq) -> ViewSquare:
        return self.squares[sq[0] * self.size + sq[1]]

    def render(self):
        if self.move is not None:
            if str_to_move(self.move[0]).direction is not None:
                self.animate(self.move[0], self.move[1])
        self.canvas.delete("all")
        for s, a in zip(self.squares, self.actives):
            s.render(a)
        self.canvas.create_line(3, 3, self.winfo_width(), 3, tags="line")
        self.canvas.create_line(3, 3, 3, self.winfo_height(), tags="line")
        self.actives = [False for _ in range(self.size ** 2)]
