import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.stats import skewnorm
import random


class ArrivalDistribution():
    def __init__(self, size, loc, scale):
        self.distribution = []
        # Randomly sample from a normal distrubtion but ensure it is a valid time
        for i in range(size + 1):
            valid = False
            while not valid:
                a = np.random.normal(size=1, loc=loc, scale=scale)[0]
                print(a)
                if (a > 0 and a < 720):
                    valid = True
                    self.distribution.append(a)

        self.distribution = np.sort(self.distribution)
        self.intervals = np.diff(self.distribution)

    def next(self, curr):
        for i in self.distribution:
            if (curr < i):
                return i

    def get_interval(self):
        t = self.intervals[0]
        self.intervals = np.delete(self.intervals, 0)
        return t


class StayDistribution():
    def __init__(self):
        size = 1000
        a = skewnorm.rvs(-5, loc=60, scale=20, size=int(size * 0.7))
        b = skewnorm.rvs(-8, loc=120, scale=15, size=int(size * 0.3))
        self.distribution = np.concatenate((a, b), axis=0)

    def get_stay_duration(self):
        return np.random.choice(self.distribution, 1)[0]


class FoodDistribution():
    def __init__(self):
        size = 1000
        arr = [0] * 12
        self.prob_arr = []
        # Lunch peak
        a = np.random.normal(
            size=int(size * 0.4),
            loc=13.5,
            scale=1.5
        )
        # Dinner peak
        b = np.random.normal(
            size=int(size * 0.6),
            loc=19.5,
            scale=1.5
        )
        self.distribution = np.concatenate((a, b), axis=0)
        for elem in self.distribution:
            if(round(elem) >= 12 and round(elem) <= 24):
                arr[int(round(elem)) - 1 - 12] += 1

        for count in arr:
            self.prob_arr.append((count / size) + 0.2)

    def get_food_probability(self, curr_time):
        if (curr_time / 60 > 0 and curr_time / 60 < 12):
            return self.prob_arr[int(curr_time / 60) - 1]
        else:
            return self.prob_arr[int(11)]


class DrinkDistribution():

    def __init__(self):
        size = 1000
        arr = [0] * 12
        self.prob_arr = []
        # First peak near lunch time
        a = np.random.normal(
            size=int(size * 0.2),
            loc=14.5,
            scale=2
        )
        # Second peak later into the night
        b = skewnorm.rvs(-7, loc=23, scale=2, size=int(size * 0.8))

        self.distribution = np.concatenate((a, b), axis=0)

        for elem in self.distribution:
            if (round(elem) >= 12 and round(elem) <= 24):
                arr[int(round(elem)) - 1 - 12] += 1

        for count in arr:
            self.prob_arr.append((count / size) + 0.15)

    def get_drink_probability(self, curr_time):
        if (curr_time / 60 > 0 and curr_time / 60 < 12):
            return self.prob_arr[int(curr_time / 60) - 1]
        else:
            return self.prob_arr[int(11)]


def select_drink(options):
    index = random.randint(1, len(options))
    return options[index]


def select_food(options):
    index = random.randint(1, len(options))
    return options[index]


if __name__ == '__main__':
    # Arrivals
    arrivals = ArrivalDistribution(48, 6.8339 * 60, 4.40638 * 60)
    sns.distplot(arrivals.distribution, bins=12)
    plt.draw()
    plt.show()

    # Length of stay
    stay = StayDistribution()
    sns.distplot(stay.distribution)
    plt.draw()
    plt.show()
    
    
    # Food
    foods = FoodDistribution()
    sns.distplot(foods.distribution, bins=12)
    p1 = foods.get_food_probability(600)
    p2 = foods.get_food_probability(200)
    p3 = foods.get_food_probability(1140)
    print("{} {} {}".format(p1, p2, p3))
    plt.draw()
    plt.show()

    # Drinks
    drinks = DrinkDistribution()
    p1 = drinks.get_drink_probability(600)
    p2 = drinks.get_drink_probability(200)
    print(p1)
    print(p2)
    sns.distplot(drinks.distribution, bins=12)
    plt.draw()
    plt.show()
