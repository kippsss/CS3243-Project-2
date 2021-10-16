# CS3243 Introduction to Artificial Intelligence
# Project 2

import Queue
import sys
import copy


# Running script: given code can be run with the command:
# python file.py, ./path/to/init_state.txt ./output/output.txt

class Sudoku(object):
    def __init__(self, puzzle):
        self.puzzle = puzzle  # self.puzzle is a list of lists
        self.ans = copy.deepcopy(puzzle)  # self.ans is a list of lists
        self.neighbours = {}

    def solve(self):
        # Obtain each variable's neighbours, the board's unassigned
        # variables. and all variable domains in this next function
        self.neighbours, unassigned, domains = self.initialise_neighbours_unassigned_domains(self.puzzle)
        # Re-update the domains after forward checking
        domains = self.initial_forward_checking(self.puzzle, domains, unassigned)
        # Begin backtracking with inference with all the information found previously
        self.ans = self.backtracking_with_inference(self.puzzle, domains, unassigned)
        self.print_puzzle(self.ans)
        return self.ans

    def initial_forward_checking(self, board, domains, unassigned):
        q = Queue.Queue()  # q contains pairs of all the assigned variables with its unassigned neighbours
        for row in range(9):
            for col in range(9):
                if board[row][col] != 0:  # If var has a pre-assigned value
                    for neighbour in self.neighbours[(row, col)]:
                        if neighbour in unassigned:
                            # If neighbour if pre-assigned value is not assigned a value yet, then pair them up in queue
                            q.put(((row, col), neighbour))
        # For every pair of assigned variable and its unassigned neighbour,
        # reduce the domain of the unassigned neighbour
        # if the value of the assigned variable is currently in the domain of the unassigned neighbour.
        while not q.empty():
            (assigned_var, unassigned_neighbour) = q.get()
            assigned_var_value = board[assigned_var[0]][assigned_var[1]]
            if assigned_var_value in domains[unassigned_neighbour]:
                domains[unassigned_neighbour].remove(assigned_var_value)
                domain_length = len(domains[unassigned_neighbour])
                if domain_length == 0:
                    # If it results in a variable not having any values in its domain,
                    # the sudoku problem cannot be solved, thus return failure
                    return "failure"
                elif domain_length == 1:
                    # If the neighbours domain length becomes a single value, it means it MUST be assigned that value.
                    # In that case, check all its neighbours and re-evaluate
                    # their domains because of this new assignment.
                    new_assigned_var = unassigned_neighbour
                    new_neighbours = self.neighbours[unassigned_neighbour]
                    for new_var in new_neighbours:
                        if new_neighbours != unassigned_neighbour:
                            q.put((new_assigned_var, new_var))
                else:
                    continue
        return domains

    def forward_checking(self, var, val, domains, removed_from_domains):
        neighbours = self.neighbours[var]
        for neighbour_var in neighbours:
            if val in domains[neighbour_var]:
                # Remove value from neighbours' domain
                domains[neighbour_var].remove(val)
                if neighbour_var not in removed_from_domains.keys():
                    removed_from_domains[neighbour_var] = set()
                # Keep track of which values we remove from any neighbours' domain so that
                # we can restore them if we backtrack
                removed_from_domains[neighbour_var].add(val)
                # If any removal of values from a neighbour's domain results in the neighbour having
                # no more values to take up, the forward checking returns failure as the problem cannot
                # be completed with the current assignment
                if len(domains[neighbour_var]) == 0:
                    return "failure"
        # Return updated domains from forward checking
        return domains

    def backtracking_with_inference(self, board, domains, unassigned):
        # If all values assigned successfully, problem solved.
        if len(unassigned) == 0:
            return board

        # Pick most constraiined variable to assign first
        var = self.most_constrained_var(domains, unassigned)
        # Keep track of which values are removed from which variable's domains, in case we need to backtrack
        # and restore them,  it can be done.
        removed_from_domains = {}

        for val in domains[var]:
            # For each value in the domain of the variable we want to assign, check first if the value is consistent
            # with the current board assignment by looking at its neighbours
            if self.is_consistent(val, var, board):
                board[var[0]][var[1]] = val
                # Maintain a copy of its domain before we edit it, so that we can easily
                # restore it when we backtrack
                var_domain_copy = copy.copy(domains[var])
                # Change domain of var to only include the consistent value (this is now an assignment)
                domains[var] = {val}

                # Derive result of forward checking
                forward_checking_result = self.forward_checking(var, val, domains, removed_from_domains)
                if forward_checking_result != "failure":
                    # If forward checking returns new domains and does not fail,
                    # recur backtracking function with this new assignment and new domains

                    result = self.backtracking_with_inference(board, domains, unassigned)
                    if result != "failure":
                        # If result will does not fail, successful assignment, thus return the result
                        return result

                # Because forward checking leads to failure, or result of pursuing further despite initial success
                # in forward checking results in failure, we need to restore the initial domains and assignment
                # and move on to the next value to try.
                for variable in removed_from_domains:
                    # Combine current domain of var with the values that we initially removed from its domain
                    domains[variable] = domains[variable].union(removed_from_domains[variable])
                domains[var] = var_domain_copy
            # Reset the value of var to 0 (unassigned) to try the next value
            board[var[0]][var[1]] = 0

        # If all values fail to qualify as a valid assignment, put the variable back into the unassigned
        # list and return failure
        unassigned.append(var)
        return "failure"

    def is_consistent(self, val, var, board):
        # Check values of all its neighbours and make sure they are not the same as the value of the
        # variable we are currently assigning a value to
        for neighbour in self.neighbours[var]:
            if val == board[neighbour[0]][neighbour[1]]:
                return False
        return True

    def most_constrained_var(self, domains, unassigned):
        smallest_domain = 10
        var_with_smallest_domain = None

        # Check all unassigned variables, return the variable with the smallest domain
        for var in unassigned:
            var_domain = domains[var]
            if len(var_domain) < smallest_domain:
                var_with_smallest_domain = var
                smallest_domain = len(var_domain)
        # Remove this variable from the unassigned list as we are about to assign
        # it a value in the backtracking_with_inference function
        unassigned.remove(var_with_smallest_domain)
        return var_with_smallest_domain

    def initialise_neighbours_unassigned_domains(self, board):
        neighbours_dict = {}
        unassigned_list = []
        domain_dict = {}

        for row in range(9):
            for col in range(9):
                # Code concerning NEIGHBOURS
                neighbours_list = []
                row_col = (row, col)
                subgrid = self.find_subgrid(row, col)
                val = board[row][col]
                for a in range(9):
                    for b in range(9):
                        c = self.find_subgrid(a, b)
                        if row_col == (a, b):
                            # potential neighbour is itself
                            continue
                        elif a == row_col[0] or b == row_col[1] or c == subgrid:
                            # potential neighbour has same row / col / subgrid
                            neighbours_list.append((a, b))
                        else:
                            # potential neighbour does not have any same row / col / subgrid, it is not a neighbour
                            continue
                neighbours_dict[row_col] = neighbours_list

                # Code concerning UNASSIGNED
                if val == 0:
                    unassigned_list.append(row_col)
                    domain_dict[row_col] = {1, 2, 3, 4, 5, 6, 7, 8, 9}
                else:
                    domain_dict[row_col] = {val}

        return neighbours_dict, unassigned_list, domain_dict

    def find_subgrid(self, a, b):
        if (0 <= a <= 2) and (0 <= b <= 2):
            return 0
        elif (0 <= a <= 2) and (3 <= b <= 5):
            return 1
        elif (0 <= a <= 2) and (6 <= b <= 8):
            return 2
        elif (3 <= a <= 5) and (0 <= b <= 2):
            return 3
        elif (3 <= a <= 5) and (3 <= b <= 5):
            return 4
        elif (3 <= a <= 5) and (6 <= b <= 8):
            return 5
        elif (6 <= a <= 8) and (0 <= b <= 2):
            return 6
        elif (6 <= a <= 8) and (3 <= b <= 5):
            return 7
        elif (6 <= a <= 8) and (6 <= b <= 8):
            return 8

    def print_puzzle(self, puzzle):
        for row in zip(puzzle):
            print (row)

if __name__ == "__main__":
    # STRICTLY do NOT modify the code in the main function here
    if len(sys.argv) != 3:
        print ("\nUsage: python CS3243_P2_Sudoku_XX.py input.txt output.txt\n")
        raise ValueError("Wrong number of arguments!")

    try:
        f = open(sys.argv[1], 'r')
    except IOError:
        print ("\nUsage: python CS3243_P2_Sudoku_XX.py input.txt output.txt\n")
        raise IOError("Input file not found!")

    puzzle = [[0 for i in range(9)] for j in range(9)]
    lines = f.readlines()

    i, j = 0, 0
    for line in lines:
        for number in line:
            if '0' <= number <= '9':
                puzzle[i][j] = int(number)
                j += 1
                if j == 9:
                    i += 1
                    j = 0

    sudoku = Sudoku(puzzle)
    ans = sudoku.solve()

    with open(sys.argv[2], 'a') as f:
        for i in range(9):
            for j in range(9):
                f.write(str(ans[i][j]) + " ")
            f.write("\n")
