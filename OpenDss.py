# Python Sudoku solver and generator written by Matthew Havard.
import random

class Sudoku:
    """
    Main class for solving Sudoku puzzles
    """
    def __init__(self, board = None):
        """
        Initialize the board.  Fill in with zeros if there is no board.
        Board can be a 2d list or a string.
        """
        if type(board) is list:
            self.board = board
        elif type(board) is str:
            self.board = [[int(e) for e in line] for line in board.split()]
        else:
            self.board = [[0 for i in range(9)] for i in range(9)]

    
    def print_board(self, print_me = True, return_me = False):
        """
        Prints the board or returns the string to be printed.
        The returned string is useful for the __str__ method
        """
        s = ''
        for i in range(len(self.board)):
            if i%3 == 0:
                s += "+==="*9+"+\n"
            else:
                s += "+---"*9+"+\n"
            row = self.board[i]
            for j in range(len(row)):
                if j%3 == 0:
                    s += "|"
                else:
                    s += ":"
                s += " {0} ".format(row[j] if row[j] != 0 else ' ')
            s += "|\n"
        s += "+==="*9+"+"
        if print_me:
            print s
        if return_me:
            return s

    def is_complete(self):
        return self.is_filled() and self.is_valid()
    
    def is_filled(self):
        """
        Only checks if all squares are filled in.  
        Does not check if the solved puzzle is valid.
        """
        for i in range(len(self.board)):
            for j in range(len(self.board)):
                if self.board[i][j] == 0:
                    return False
        return True
    
    def is_valid(self):
        """
        Checks if puzzle is valid.  May not be a completely filled in puzzle.
        """
        return self.check_something(True) and self.check_something(False) and self.check_box()

    def find_item(self, i, j, row):
        """
        Helper func for self.check_something
        """
        return self.board[i][j] if row else self.board[j][i]

    def check_something(self, row):
        """
        If row is True, checks if the rows of the puzzle are valid.
        Otherwise checks if the columns of the puzzle are valid.
        """
        for i in range(len(self.board)):
            in_b = []
            for j in range(len(self.board)):
                e = self.find_item(i, j, row)
                if e != 0 and (e in in_b or e < 0 or e > 9):
                    
                    return False
                else:
                    in_b.append(e)
        return True

    def check_box(self):
        """
        Checks if the boxes of the puzzle are valid
        """
        for r_lower_limit in range(0, 8, 3):
            for c_lower_limit in range(0, 8, 3):
                in_box = []
                for r in range(r_lower_limit, r_lower_limit+3):
                    for c in range(c_lower_limit, c_lower_limit+3):
                        e = self.board[r][c]
                        if e != 0 and (e in in_box or e < 0 or e > 9):
                            return False
                        else:
                            in_box.append(e)
        return True

    def __str__(self):
        """
        String method so that you can just do print sudoku
        """
        return self.print_board(False, True)

    def __getitem__(self, i):
        """
        Gets a row of the puzzle
        """
        return self.board[i]

    def my_setitem(self, i, j, value):
        """
        Sets a square in the puzzle to a certain value
        """
        if value != 0:
            if value in self.board[i]:
                
                return False
            for c in range(9):
                if value == self.board[c][j]:
                    
                    return False
            for r in range(i/3*3, i/3*3+3):
                for c in range(j/3*3, j/3*3+3):
                    if value == self.board[r][c]:
                        
                        return False
        self.board[i][j] = value
        return True


def my_shuffle(l):
    """
    Helper func.  random.shuffle mutates a list without returning it,
    but I want the list returned as well.  (I don't care if the original
    is mutated.)
    """
    random.shuffle(l)
    return l

def coord(r, c):
    """
    Helper function for solutions. Returns an adjacent coordinate.
    Used to walk the squares of the puzzle.
    """
    r, c = (r if (c+1) % 9 > 0 else r+1, (c+1) % 9)
    return r, c

def copy_sudoku(sudoku):
    """
    Helper function for solutions.  Returns a copy of a soduku, which
    is useful when you want to fill in a value to test without modifying
    the original puzzle.
    """
    b = []
    for i in range(9):
        b.append(sudoku.board[i][:])
    return Sudoku(b)

def solutions(sudoku, (r, c), justone, rand_iter=False):
    """
    Returns a solution or all solutions to a Sudoku puzzle.
    More than one solution would mean it is not a valid puzzle
    and needs more squares filled in at the start.
    """
    all_sols = []
    if sudoku[r%9][c%9] != 0 and sudoku.is_complete():
        return sudoku if justone else [sudoku]
    else:
        while sudoku[r][c] != 0:
            r, c = coord(r, c)
        for v in (my_shuffle(range(1, 10)) if rand_iter else range(1, 10)):
            if sudoku.my_setitem(r, c, v):
                s = solutions(copy_sudoku(sudoku),
                              coord(r, c),
                              justone,
                              rand_iter)
                if justone and s:
                    return s
                else:
                    all_sols.extend(s)
    return all_sols

def random_solved_puzzle():
    return solutions(Sudoku(), (0,0), True, True)

def random_unsolved_puzzle():
    """
    Generates a random, very difficult Sudoku puzzle with as many blank
    squares as possible, while making sure the puzzle has a unique solution.
    May take several minutes as the algorithm is pretty randomized.
    """
    print "Generating random sudoku puzzle.  May take several minutes..."
    solution = random_solved_puzzle()
    possible_coords = [(r,c) for r in range(9) for c in range(9)]
    random.shuffle(possible_coords)
    while possible_coords:
        r, c = possible_coords.pop()
        print "Number of squares considered for removal:", len(possible_coords)
        v = solution[r][c]
        solution.my_setitem(r, c, 0)
        if len(solutions(copy_sudoku(solution), (0,0), False)) > 1:
            solution.my_setitem(r, c, v)
    return solution

if __name__ == "__main__":
	s = ""
	for i in range(9):
		s += raw_input("")+"\n"
	board = Sudoku(s)
	print "Solving:\n",board
	solved = solutions(copy_sudoku(board), (0,0), True)
	print solved
