from pulp import *

if __name__ == "__main__":

    x1 = LpVariable('x1', lowBound=0, cat='Continuous')
    x2 = LpVariable('x2', lowBound=0, cat='Continuous')

    example1 = LpProblem("example1", LpMaximize)

    example1 += 3 * x1 + 5 * x2

    example1 += x1 <= 4
    example1 += x2 <= 6
    example1 += 3 * x1 + 2 * x2 <= 18

    example1.solve()

    print("Status: ", LpStatus[example1.status])

    for v in example1.variables():
        print(v.name, "=", v.varValue)

    print("Objective value Example 1 = ", value(example1.objective))