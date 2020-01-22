import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
from scipy.stats import skewnorm 

#a = np.random.gamma(120, 0.5, 1000)
#b = np.random.gamma(120, 0.3, 1000)
#c = np.random.gamma(120, 1, 1000)

def one():
    size = 1000

    a = skewnorm.rvs(-5, loc=60, scale=20, size=int(size * 0.7))
    b = skewnorm.rvs(-8, loc=120, scale=15, size=int(size * 0.3))

    combined = np.concatenate((a, b), axis=0)
    test = np.array([])
    print(combined)
    for i in range(0, 1000):
        e = np.random.choice(combined, 1)
        print(e)
        test = np.append(test, e)

    print(test)

    sns.distplot(test, bins=24)
    plt.draw()
    plt.show()

def two():
    a = np.random.normal(7, 6, 1000)
    print(a)

    counts = [0] * 100
    print(counts)
    for num in a:
        index = int(round(num, 0))
        if (index >= 0):
            counts[index] += 1
    print(counts)

    sns.distplot(a, bins=12)
    plt.show()
    print("nice")


two()
