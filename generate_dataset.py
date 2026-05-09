import pandas as pd
import random

data = []

for i in range(500):

    power = random.randint(50, 3000)
    hours = round(random.uniform(1, 24), 2)

    units = (power * hours) / 1000
    bill = units * 10

    data.append([power, hours, units, bill])

df = pd.DataFrame(
    data,
    columns=['Power', 'Hours', 'Units', 'Bill']
)

df.to_csv('dataset/energy_data.csv', index=False)

print("Dataset Generated Successfully")