import sys

from crossword import *

from collections import deque


class CrosswordCreator():

    def __init__(self, crossword):
        """
        Create new CSP crossword generate.
        """
        self.crossword = crossword
        self.domains = {
            var: self.crossword.words.copy()
            for var in self.crossword.variables
        }

    def letter_grid(self, assignment):
        """
        Return 2D array representing a given assignment.
        """
        letters = [
            [None for _ in range(self.crossword.width)]
            for _ in range(self.crossword.height)
        ]
        for variable, word in assignment.items():
            direction = variable.direction
            for k in range(len(word)):
                i = variable.i + (k if direction == Variable.DOWN else 0)
                j = variable.j + (k if direction == Variable.ACROSS else 0)
                letters[i][j] = word[k]
        return letters

    def print(self, assignment):
        """
        Print crossword assignment to the terminal.
        """
        letters = self.letter_grid(assignment)
        for i in range(self.crossword.height):
            for j in range(self.crossword.width):
                if self.crossword.structure[i][j]:
                    print(letters[i][j] or " ", end="")
                else:
                    print("█", end="")
            print()

    def save(self, assignment, filename):
        """
        Save crossword assignment to an image file.
        """
        from PIL import Image, ImageDraw, ImageFont
        cell_size = 100
        cell_border = 2
        interior_size = cell_size - 2 * cell_border
        letters = self.letter_grid(assignment)

        # Create a blank canvas
        img = Image.new(
            "RGBA",
            (self.crossword.width * cell_size,
             self.crossword.height * cell_size),
            "black"
        )
        font = ImageFont.truetype("assets/fonts/OpenSans-Regular.ttf", 80)
        draw = ImageDraw.Draw(img)

        for i in range(self.crossword.height):
            for j in range(self.crossword.width):

                rect = [
                    (j * cell_size + cell_border,
                     i * cell_size + cell_border),
                    ((j + 1) * cell_size - cell_border,
                     (i + 1) * cell_size - cell_border)
                ]
                if self.crossword.structure[i][j]:
                    draw.rectangle(rect, fill="white")
                    if letters[i][j]:
                        _, _, w, h = draw.textbbox((0, 0), letters[i][j], font=font)
                        draw.text(
                            (rect[0][0] + ((interior_size - w) / 2),
                             rect[0][1] + ((interior_size - h) / 2) - 10),
                            letters[i][j], fill="black", font=font
                        )

        img.save(filename)

    def solve(self):
        """
        Enforce node and arc consistency, and then solve the CSP.
        """
        self.enforce_node_consistency()
        self.ac3()
        return self.backtrack(dict())

    def enforce_node_consistency(self):
        """
        Update `self.domains` such that each variable is node-consistent.
        (Remove any values that are inconsistent with a variable's unary
         constraints; in this case, the length of the word.)
        """
        for var in self.crossword.variables.copy():
            length = var.length
            for word in self.domains[var].copy():
                if len(word) != length:
                    self.domains[var].remove(word)

    def revise(self, x, y):
        """
        Make variable `x` arc consistent with variable `y`.
        To do so, remove values from `self.domains[x]` for which there is no
        possible corresponding value for `y` in `self.domains[y]`.

        Return True if a revision was made to the domain of `x`; return
        False if no revision was made.
        """
        revision = False
        overlap = self.crossword.overlaps[x, y]
        if overlap:
            i, j = overlap
            for word in self.domains[x].copy():
                charx = word[i]
                if all(y_word[j] != charx for y_word in self.domains[y]):
                    self.domains[x].remove(word)
                    revision = True
        return revision

    def ac3(self, arcs=None):
        """
        Update `self.domains` such that each variable is arc consistent.
        If `arcs` is None, begin with initial list of all arcs in the problem.
        Otherwise, use `arcs` as the initial list of arcs to make consistent.

        Return True if arc consistency is enforced and no domains are empty;
        return False if one or more domains end up empty.
        """
        # check if arc is given or not
        if arcs == None:
            arcs = deque()
            # build arcs
            for var in self.crossword.variables:
                for neighbor in self.crossword.neighbors(var):
                    arcs.append((var, neighbor))
        else:
            arcs = deque(arcs)
        # run ac3
        # until all arcs are empty
        while arcs:
            x, y = arcs.popleft()
            # checking if arc concistency is maintained in two variables
            if self.revise(x, y):
                if not self.domains[x]:
                    return False
                neighbors = self.crossword.neighbors(x).copy()
                neighbors.remove(y)
                for z in neighbors:
                    arcs.append((z, x))
        return True

    def assignment_complete(self, assignment):
        """
        Return True if `assignment` is complete (i.e., assigns a value to each
        crossword variable); return False otherwise.
        """
        # check this implementation again
        for variable in self.crossword.variables:
            if not (assignment.get(variable, False)):
                return False
        return True

    def consistent(self, assignment):
        """
        Return True if `assignment` is consistent (i.e., words fit in crossword
        puzzle without conflicting characters); return False otherwise.
        """
        items = set()
        for key, value in assignment.items():
            items.add(value)
            if len(value) != (key.length):
                return False
            neighbors = self.crossword.neighbors(key)
            for neighbor in neighbors:
                overlap = self.crossword.overlaps[key, neighbor]
                if overlap:
                    i, j = overlap
                    neig_value = assignment.get(neighbor, False)
                    if neig_value:
                        if value[i] != neig_value[j]:
                            return False
        
        if len(items) != len(assignment.values()):
            return False

        return True                     
        
    def order_domain_values(self, var, assignment):
        """
        Return a list of values in the domain of `var`, in order by
        the number of values they rule out for neighboring variables.
        The first value in the list, for example, should be the one
        that rules out the fewest values among the neighbors of `var`.
        """
        # creating copy of domain
        domain = self.domains[var].copy()

        # key function to find least constraining
        def least_constraning(value):
            nonlocal var
            n = 0
            neighbors = self.crossword.neighbors(var)
            for z in neighbors:
                i, j = self.crossword.overlaps[var, z]
                for word in self.domains[z]:
                    if value[i] != word[j]:
                        n += 1
            return n
        
        # actually sortying using the above key
        sorted_domain = sorted(domain, key=least_constraning)
        return sorted_domain

        return self.domains[var].copy()

    def select_unassigned_variable(self, assignment):
        """
        Return an unassigned variable not already part of `assignment`.
        Choose the variable with the minimum number of remaining values
        in its domain. If there is a tie, choose the variable with the highest
        degree. If there is a tie, any of the tied variables are acceptable
        return values.
        """
        variables = self.crossword.variables.copy()
        # sorting variables  according to heuristics
        variables = sorted(variables, key=lambda x: [len(self.domains[x]), len(self.crossword.neighbors(x))])
        # choosing non-assigned variable
        for var in variables:
            if not assignment.get(var, False):
                return var        

    def backtrack(self, assignment):
        """
        Using Backtracking Search, take as input a partial assignment for the
        crossword and return a complete assignment if possible to do so.

        `assignment` is a mapping from variables (keys) to words (values).

        If no assignment is possible, return None.
        """
        if self.assignment_complete(assignment):
            return assignment
        # select unassigned variable
        var = self.select_unassigned_variable(assignment)
        # loop through its domain
        for value in self.order_domain_values(var, assignment):
            temp = assignment.copy()
            temp[var] = value
            # if value is consistent to then answer 
            if self.consistent(temp):
                assignment[var] = value
                result = self.backtrack(assignment)
                # if result is not failure
                if result:
                    return result
                assignment[var] = ""
        return None


def main():

    # Check usage
    if len(sys.argv) not in [3, 4]:
        sys.exit("Usage: python generate.py structure words [output]")

    # Parse command-line arguments
    structure = sys.argv[1]
    words = sys.argv[2]
    output = sys.argv[3] if len(sys.argv) == 4 else None

    # Generate crossword
    crossword = Crossword(structure, words)
    creator = CrosswordCreator(crossword)
    assignment = creator.solve()

    # Print result
    if assignment is None:
        print("No solution.")
    else:
        creator.print(assignment)
        if output:
            creator.save(assignment, output)


if __name__ == "__main__":
    main()
