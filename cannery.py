from pulp import *

if __name__ == "__main__":

    I = 8
    J = 10
    maximumPlant = 3

    #need data to work but too lazy
    distances = []
    for i in range(I):
        distancesForI = []
        for j in range(J):
            distancesForI.append(0)
        distances.append(distancesForI)

    demand = [0 for _ in range(J)]
    plantInfo = [[0, 0] for _ in range(I)]


    doUsePlant = []
    for i in range(I):
        doUsePlant.append(LpVariable('doUsePlant' + str(i), lowBound=0, upBound=1, cat='Integer'))

    amountToSend = []
    for i in range(I):
        sendFromPlant = []
        for j in range(J):
            sendFromPlant.append(LpVariable('From ' + str(i) + ' to ' + str(j), lowBound=0, cat='Continuous'))
        amountToSend.append(sendFromPlant)

    cannery = LpProblem("cannery", LpMinimize)

    totalMilesSum = 0
    for i in range(I):
        for j in range(J):
            totalMilesSum += 90*amountToSend[i][j]*distances[i][j] + plantInfo[i][0]*doUsePlant[i]

    cannery += totalMilesSum

    for i in range(I):
        sumPerPlant = 0
        for j in range(J):
            sumPerPlant += amountToSend[i][j]
        cannery += sumPerPlant <= plantInfo[i][1]

    for j in range(J):
        sumReceived = 0
        for i in range(I):
            sumReceived += amountToSend[i][j]
        cannery += sumReceived >= demand[j]

    totalUsed = 0
    for doUse in doUsePlant:
        totalUsed += doUse

    cannery += totalUsed == 3

    cannery.solve()

    print("Status: ", LpStatus[cannery.status])

    for v in cannery.variables():
        print(v.name, "=", v.varValue)

    print("Objective value Example 1 = ", value(cannery.objective))