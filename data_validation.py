import os
import json
import pandas as pd
import matplotlib.pyplot as plt

def main(): 
    # read text file
    with open("recording_2025-11-30T19_41_39+00_00_b2bd18", "r") as f:
        data = f.read()

    # get first line
    first_line = data.split("\n")[0]

    data = [json.loads(line) for line in data.split("\n") if line]

    df = pd.DataFrame(data)

    print(df.head())

    plt.figure(figsize=(10, 6))
    plt.plot(df['timestamp'], df['probability'])
    plt.xlabel('Timestamp')
    plt.ylabel('Probability')
    plt.title('Prediction Probability Over Time')
    plt.show()

if __name__ == "__main__":
    main()
