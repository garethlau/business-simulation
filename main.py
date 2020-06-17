import math
import random
import simpy
import numpy as np
from distributions import ArrivalDistribution, StayDistribution, select_drink, select_food, DrinkDistribution, FoodDistribution

'''
SUMMARY

- Customer groups come according to normal distribution
- Customer groups will stay for an amount of time according to a duration distribution
- Customer groups have a number of people ranging from 4 to 8 customers
- Each customer has a __% of buying alcohol at any given time bvased on a frequency distribution
- Each customer has a __% chance of buying food at any given time based on a frequency distribution
- When a customer orders food, it requests an Employee. The employee then must request a fryer to start frying the food
- If all staff are occupied and a new group arrives, staff making food or serving drinks will be interupted

DEFENITIONS

- POD: max seating for 8 people
- FRYER: deep frier
- Party: Group of Customers

'''


def space(string, length):
    res = str(string)
    missing = length - len(res)

    for i in range(0, missing):
        res += " "

    return res


def print_event(id, time, message):
    print("[ {} | {} ] {}".format(
        space(round(time / 60, 3), 10), space(id, 20), message))


def customer(env, data, pod_id, id, staff, fryers):

    is_drinking = False
    is_eating = False
    order = None
    drink = None

    # At a given point in time, how likely will someone buy a drink?
    if random.uniform(0, 1) < drinkDistribution.get_drink_probability(env.now):
        is_drinking = True
        # Choose the drink
        drink = select_drink(DRINK_ITEMS)
        data['orders']['drinks'].append(drink)

    if (random.uniform(0, 1) < foodDistribution.get_food_probability(env.now)):
        is_eating = True
        # Choose the food
        order = select_food(FOOD_ITEMS)
        data['orders']['foods'].append(order)

    if (is_eating and is_drinking):
        while is_eating:
            try:
                # request a staff to get a drink and make an order
                # for sake of simplicity, assume that the staff is able to
                # pour a drink while frying
                staff_request = staff.request(priority=PRIORITIES["food"])
                order_request_time = env.now
                print_event("POD: {} Customer: {}".format(pod_id, id),
                            env.now, "{} and {} Requested".format(order["name"], drink['name']))
                yield staff_request

                # Staff is available, now request a fryer
                fryer_request = fryers.request()
                yield fryer_request

                # Start frying the item
                # Assume that the staff is able to grab the drink during this time
                print_event("POD: {} Customer: {}".format(pod_id, id), env.now,
                            "{} Started Frying".format(order["name"]))
                yield env.timeout(order["duration"])

                # Order completed, release
                is_eating = False
                is_drinking = False
                print_event("POD: {} Customer: {}".format(pod_id, id), env.now,
                            "{} and {} Served (Wait: {})".format(order["name"], drink["name"], env.now - order_request_time))
                staff.release(staff_request)
                fryers.release(fryer_request)

                # Log the completed order
                data['sales']['drinks'].append(drink)
                data['sales']['foods'].append(order)
                data['wait']['foods'].append(
                    (env.now - order_request_time) - order['duration'])

            except simpy.Interrupt:
                print_event("POD: {} Customer: {}".format(pod_id, id), env.now,
                            "(INTERRUPT) {} Service".format(order["name"]))
                staff.release(staff_request)

    elif (is_drinking):
        while is_drinking:
            try:
                # request a staff to get a drink
                staff_request = staff.request(priority=PRIORITIES["drinks"])
                drink_request_time = env.now
                print_event("POD: {} Customer: {}".format(
                    pod_id, id), env.now, "{} Requested".format(drink['name']))
                yield staff_request

                # pour beer
                yield env.timeout(INTERACTION_TIME['serve_beer'])

                # all done, release
                print_event("POD: {} Customer: {}".format(pod_id, id), env.now,
                            "{} Served (Waited: {})".format(drink['name'], env.now - drink_request_time))
                is_drinking = False
                staff.release(staff_request)

                # Log the completed order
                data['sales']['drinks'].append(drink)
                data['wait']['drinks'].append(
                    (env.now - drink_request_time) - INTERACTION_TIME['serve_beer'])

            except simpy.Interrupt:
                print_event("POD: {} Customer: {}".format(pod_id, id), env.now,
                            "(INTERRUPT) {} Service".format(drink['name']))
                staff.release(staff_request)

    elif (is_eating):
        while is_eating:
            try:
                # Request a staff
                staff_request = staff.request(priority=PRIORITIES["food"])
                order_request_time = env.now
                print_event("POD: {} Customer: {}".format(pod_id, id),
                            env.now, "{} Requested".format(order["name"]))
                yield staff_request

                # Staff is available, now request a fryer
                fryer_request = fryers.request()
                yield fryer_request

                # Start frying the item
                print_event("POD: {} Customer: {}".format(pod_id, id), env.now,
                            "{} Started Frying".format(order["name"]))
                yield env.timeout(order["duration"])

                # Order completed, release
                is_eating = False
                print_event("POD: {} Customer: {}".format(pod_id, id), env.now,
                            "{} Served (Wait: {})".format(order["name"], env.now - order_request_time))
                staff.release(staff_request)
                fryers.release(fryer_request)

                # Log the completed order
                data['sales']['foods'].append(order)
                data['wait']['foods'].append(
                    (env.now - order_request_time) - order['duration'])

            except simpy.Interrupt:
                print_event("POD: {} Customer: {}".format(pod_id, id), env.now,
                            "(INTERRUPT) {} Service".format(order["name"]))
                staff.release(staff_request)


def party(env, data, id, pods, staff, fryers):
    data['parties']['arrived'] += 1
    # visit duration
    visit_duration = stayDistribution.get_stay_duration()

    arrive_time = env.now

    patience = 30

    # create customers
    group_size = random.randint(*CUSTOMERS_PER_GROUP)
    data["customers"]['arrived'] += group_size

    # Get staff to introduce them
    print_event("POD: {}".format(id), env.now, "Staff Requested to Intro")
    staff_request = staff.request(priority=PRIORITIES["pods"], preempt=True)

    # Staff welcomes the party of customers
    yield env.timeout(INTERACTION_TIME['welcome'])

    # Staff leaves and lets the party wait for a pod
    staff.release(staff_request)  # staff leaves
    pod_request = pods.request()    # part continues to wait for a pod
    print_event("POD: {}".format(id), env.now, "Pod Requested")

    # If a pod opens up, request a staff
    results = yield pod_request | env.timeout(patience)
    if pod_request in results:
        # There is an open pod
        # Request a staff
        staff_request = staff.request(
            priority=PRIORITIES["pods"], preempt=True)
        yield staff_request

        # Staff shows the party to the pod
        yield env.timeout(INTERACTION_TIME['show_to_pod'])

        # Staff showed the party to the pod, release
        staff.release(staff_request)

        # Party uses the pod
        seated_time = env.now
        print_event("POD: {}".format(id), env.now,
                    "Pod Served (Waited: {})".format(seated_time - arrive_time))

        # Admission sales
        data['sales']['admission'] += (math.ceil(visit_duration / 60)
                                       * ADMISSION_PRICE * group_size)
        data['wait']['pods'].append(seated_time - arrive_time)

        for i in range(group_size):
            c = customer(env, data, id, i, staff, fryers)
            env.process(c)

        yield env.timeout(visit_duration)

        # release the resources
        print_event("POD: {}".format(id), env.now, "Used Pod for: {} minutes".format(env.now - seated_time))
        pods.release(pod_request)

    else:
        pods.release(pod_request)
        data['parties']['left'] += 1
        data['customers']['left'] += group_size
        print_event("POD: {}".format(id), env.now,
                    "Left (Waited: {})".format(env.now - arrive_time))


def generator(env, data, num, pods, staff, fryers):
    for i in range(0, num):
        p = party(env, data, i, pods, staff, fryers)
        env.process(p)
        yield env.timeout(arrivalDistribution.get_interval())


class MonitoredResource(simpy.PreemptiveResource):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.data = []

    def request(self, *args, **kwargs):
        self.data.append((self._env.now, len(self.queue)))
        return super().request(*args, **kwargs)

    def release(self, *args, **kwargs):
        self.data.append((self._env.now, len(self.queue)))
        return super().release(*args, **kwargs)


def print_summary(data):

    # Foot traffic
    arrived = data['customers']['arrived']
    left = data['customers']['left']
    retain_percentage = round(((arrived - left) / arrived) * 100, 2)

    # Total revenue
    total_revenue = data['sales']['admission']
    tmp = total_revenue

    for sale in data['sales']['drinks']:
        total_revenue += sale['revenue']

    drinks_revenue = total_revenue - tmp
    tmp = total_revenue

    for sale in data['sales']['foods']:
        total_revenue += sale['revenue']

    food_revenue = total_revenue - tmp

    # Pod wait time
    pod_wait_time = 0
    for delay in data['wait']['pods']:
        pod_wait_time += (delay - 8)

    # Food wait time
    food_wait_time = 0
    for delay in data['wait']['foods']:
        food_wait_time += delay

    # Drink wait time
    drink_wait_time = 0
    for delay in data['wait']['drinks']:
        drink_wait_time += delay

    print("="*10 + " SUMMARY " + "="*10)
    print("# of Customers that Arrived: {}".format(arrived))
    print("# of Customers that Left: {}".format(left))
    print("Percent of Customers Retained: {}".format(retain_percentage))
    print("Total Time Spent Waiting for Pods: {}".format(pod_wait_time))
    print("Total Revenue: {}".format(total_revenue))

    print("="*10 + " FOOD " + "=" * 10)
    print("Food Items Ordered: {}".format(len(data['orders']['foods'])))
    print("Food Items Sold: {}".format(len(data['sales']['foods'])))
    print("Revenue from Food: {}".format(food_revenue))
    print("Food Wait: {}".format(food_wait_time))


    print("="*10 + " DRINKS " + "=" * 10)
    print("Drinks Ordered: {}".format(len(data['orders']['drinks'])))
    print("Drinks Sold: {}".format(len(data['sales']['drinks'])))
    print("Revenue from Drinks: {}".format(drinks_revenue))
    print("Drink Wait: {}".format(drink_wait_time))


if __name__ == '__main__':
    print("simpy version: {}".format(simpy.__version__))
    print("numpy version".format(np.__version__))

    # Object to store data during the simulation
    data = {
        "customers": {
            "arrived": 0,
            "left": 0
        },
        "parties": {
            "arrived": 0,
            "left": 0
        },
        "wait": {
            "drinks": [],
            "foods": [],
            "pods": []
        },
        "orders": {
            "drinks": [],
            "foods": []
        },
        "sales": {
            "drinks": [],
            "foods": [],
            "admission": 0
        }
    }
    # Store Parameters
    NUM_FRYERS = 3
    NUM_STAFF = 3
    NUM_PODS = 8
    ADMISSION_PRICE = 7

    # Set a very long sim time to account for events that overflow past the operating hours
    SIM_TIME = 10000 * 60     

    # Customer / Group Parameters
    CUSTOMERS_PER_GROUP = [4, 8]

    # Employee interaction times
    INTERACTION_TIME = {
        "welcome": 3,
        "show_to_pod": 5,
        "serve_beer": 2
    }

    # Distribution Parameters
    ARRIVAL_PARAMS = {
        "size": 100,
        "loc": 6.8339 * 60,
        "scale": 4.40638 * 60
    }

    # Environment configurations
    PRIORITIES = {
        "pods": 1,
        "drinks": 2,
        "food": 2
    }

    FOOD_ITEMS = {
        1: {
            "name": "Fries",
            "duration": 3.5,
            "revenue": 5
        },
        2: {
            "name": "Onion Rings",
            "duration": 2.25,
            "revenue": 5

        },
        3: {
            "name": "Chicken Tenders",
            "duration": 5.25,
            "revenue": 5

        },
        4: {
            "name": "Cheese Sticks",
            "duration": 5,
            "revenue": 5
        },
        5: {
            "name": "Corndogs",
            "duration": 8.5,
            "revenue": 5
        }
    }

    DRINK_ITEMS = {
        1: {
            "name": "Corona Extra",
            "revenue": 5
        },
        2: {
            "name": "Molson Canadian",
            "revenue": 4
        },
        3: {
            "name": "Budweiser",
            "revenue": 3
        },

    }

    # Environment
    env = simpy.Environment()

    # Create distributions
    np.random.seed(42)

    # Generate distributions
    arrivalDistribution = ArrivalDistribution(
        ARRIVAL_PARAMS["size"],
        ARRIVAL_PARAMS["loc"],
        ARRIVAL_PARAMS["scale"]
    )
    stayDistribution = StayDistribution()
    drinkDistribution = DrinkDistribution()
    foodDistribution = FoodDistribution()

    # Resources
    pods = simpy.Resource(env, capacity=NUM_PODS)    
    staff = MonitoredResource(env, capacity=NUM_STAFF)
    fryers = simpy.Resource(env, capacity=NUM_FRYERS)

    env.process(
        generator(env, data, ARRIVAL_PARAMS['size'], pods, staff, fryers))
    env.run(until=SIM_TIME)
    # print(staff.data)
    print_summary(data)
