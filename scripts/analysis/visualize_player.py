import pandas as pd
import matplotlib.pyplot as plt
import os

def visualize_player(player_name, year=2024):
    filename = f"data/player_gamelogs/{player_name.replace(' ', '_')}_{year}.csv"

    if not os.path.exists(filename):
        print(f"❌ File not found: {filename}")
        return

    # Load and clean
    df = pd.read_csv(filename)
    df["PTS"] = pd.to_numeric(df["PTS"], errors="coerce")
    df["Date"] = pd.to_datetime(df["Date"].str.strip(), format="%b %d", errors="coerce")
    df["Date"] = df["Date"].apply(lambda d: d.replace(year=2024) if pd.notnull(d) else d)

    # Drop bad rows
    df = df.dropna(subset=["PTS", "Date"])
    df = df.sort_values("Date")

    # Debug output
    print("\nParsed Data:")
    print(df[["Date", "PTS"]])

    # Rolling averages
    df["Rolling_3"] = df["PTS"].rolling(3).mean()
    df["Rolling_5"] = df["PTS"].rolling(5).mean()

    # Plotting
    plt.figure(figsize=(12, 6))
    plt.plot(df["Date"], df["PTS"], label="Game PTS", marker="o", linewidth=1.5)
    plt.plot(df["Date"], df["Rolling_3"], label="3-Game Avg", linestyle="--", linewidth=2)
    plt.plot(df["Date"], df["Rolling_5"], label="5-Game Avg", linestyle=":", linewidth=2)

    plt.title(f"{player_name} - {year} Points Per Game")
    plt.xlabel("Date")
    plt.ylabel("Points")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    visualize_player("Caitlin Clark")
