import sys
import os
import json
import math
import random

# Constants for file names
EVENTS_FILE = "Events.txt"
STATS_FILE = "Stats.txt"
LOG_DIR = "logs"

# Data structures to store events and statistics
events = {}
statistics = {}

def read_events(file_path):
    """Read event definitions from Events.txt."""
    with open(file_path, "r") as file:
        lines = file.readlines()
    num_events = int(lines[0].strip())
    for line in lines[1:num_events + 1]:
        parts = line.strip().split(":")
        if len(parts) != 5:
            print(f"Skipping invalid line in Events.txt: {line.strip()}")
            continue
        name, event_type, min_val, max_val, weight = parts
        events[name] = {
            "type": event_type,
            "min": float(min_val) if min_val else 0,
            "max": float(max_val) if max_val else float('inf'),
            "weight": int(weight)
        }

def read_statistics(file_path):
    """Read statistics definitions from Stats.txt."""
    with open(file_path, "r") as file:
        lines = file.readlines()
    num_stats = int(lines[0].strip())
    for line in lines[1:num_stats + 1]:
        parts = line.strip().split(":")
        if len(parts) != 4:
            print(f"Skipping invalid line in Stats.txt: {line.strip()}")
            continue
        name, mean, std_dev, _ = parts  # The last underscore is to ignore the last empty part
        statistics[name] = {
            "mean": float(mean),
            "std_dev": float(std_dev)
        }

def generate_events(days):
    """Generate events based on event definitions and statistics."""
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)
    
    for day in range(days):
        log_file = os.path.join(LOG_DIR, f"day_{day + 1}.log")
        daily_events = {}  # Dictionary to hold daily events data
        
        for event_name, event_info in events.items():
            if event_name in statistics:
                mean = statistics[event_name]["mean"]
                std_dev = statistics[event_name]["std_dev"]
                if event_info["type"] == "C":  # Continuous event
                    value = max(event_info["min"], min(random.gauss(mean, std_dev), event_info["max"]))
                    value = round(value, 2)
                else:  # Discrete event
                    value = max(int(event_info["min"]), min(int(random.gauss(mean, std_dev)), int(event_info["max"])))
                
                # Add event to the daily events dictionary
                daily_events[event_name] = value
        
        # Write events to a log file in JSON format
        with open(log_file, "w") as file:
            json.dump(daily_events, file, indent=4)
        
        # Print the daily events in JSON format
        print(f"Day {day + 1} events:")
        print(json.dumps(daily_events, indent=4))

def analyze_events(days):
    """Analyze events and calculate daily statistics."""
    events = ["Logins", "Time online", "Emails sent", "Emails opened", "Emails deleted"]
    daily_totals = {name: [] for name in events}

    for day in range(days):
        log_file = os.path.join(LOG_DIR, f"day_{day + 1}.log")
        try:
            with open(log_file, "r") as file:
                # Load the log file as JSON
                daily_data = json.load(file)

            # Accumulate values for each event
            for event_name, value in daily_data.items():
                if event_name in daily_totals:
                    daily_totals[event_name].append(value)
                else:
                    print(f"Skipping unknown event: {event_name}")

        except (json.JSONDecodeError, KeyError) as e:
            print(f"Error reading log file {log_file}: {e}")
            continue

    # Calculate baseline statistics
    baseline_statistics = {}
    for event_name, values in daily_totals.items():
        if values:  # Ensure there are values to analyze
            mean = sum(values) / len(values)
            variance = sum((x - mean) ** 2 for x in values) / len(values)
            std_dev = "{:.2f}".format(math.sqrt(variance))  # Format standard deviation to 2 decimals
            total = sum(values)
            baseline_statistics[event_name] = {
                "total": total,
                "mean": "{:.2f}".format(mean),
                "std_dev": std_dev
            }
            print(f"{event_name} - Total: {total}, Mean: {mean}, Std Dev: {std_dev}")
        else:
            print(f"No data available for event: {event_name}")


    # Display the results in JSON format
    print(json.dumps(baseline_statistics, indent=4))

    return baseline_statistics

def detect_anomalies(days, baseline_statistics):
    """Detect anomalies based on generated events and baseline statistics."""
    threshold = 2 * sum(e["weight"] for e in events.values())  # Calculate the threshold once at the start
    
    for day in range(days):
        log_file = os.path.join(LOG_DIR, f"day_{day + 1}.log")
        anomaly_counter = 0
        try:
            with open(log_file, "r") as file:
                daily_data = json.load(file)
                
            for event_name, value in daily_data.items():
                if event_name in baseline_statistics:
                    mean = float(baseline_statistics[event_name]["mean"])
                    std_dev = float(baseline_statistics[event_name]["std_dev"])
                    deviation = abs(value - mean) / std_dev if std_dev > 0 else 0
                    weight = events[event_name]["weight"] if event_name in events else 1  # Default weight is 1 if not specified
                    anomaly_counter += deviation * weight

            status = "!!!!!!!!!!!!!!!!!!!!!!!!!flagged!!!!!!!!!!!!!!!!!!!!!!!!!" if anomaly_counter >= threshold else "okay"
            print(f"Day {day + 1} - Anomaly Counter: {anomaly_counter}, Threshold: {threshold}, Status: {status}")

        except (json.JSONDecodeError, FileNotFoundError) as e:
            print(f"Error reading log file {log_file}: {e}")
            continue

def main():
    if len(sys.argv) != 4:
        print("Usage: python IDS.py <Events.txt> <Stats.txt> <days>")
        sys.exit(1)
    
    events_file = sys.argv[1]
    stats_file = sys.argv[2]
    days = int(sys.argv[3])

    read_events(events_file)
    read_statistics(stats_file)
    print("Generating events... Done! Press Enter to continue...") 
    input()  # Waits for the user to press Enter
    generate_events(days)
    print("Calculating statistics... Done! Press Enter to continue...") 
    input()  # Waits for the user to press Enter
    baseline_statistics = analyze_events(days)
    print("Detecting Anomalies... Done! Press Enter to continue...") 
    input()  # Waits for the user to press Enter
    detect_anomalies(days, baseline_statistics)
    while True:
        user_input = input("Would you like to load another statistics file (y/n)? ")
        if user_input.lower() == "y":
            new_file = input("Enter new statistics file name: ")
            read_statistics(new_file)  # Correctly read the new statistics file
            days = int(input("Enter number of days to generate events: "))
            print("Generating events... Done! Press Enter to continue...") 
            input()  # Waits for the user to press Enter
            generate_events(days)
            print("Calculating statistics... Done! Press Enter to continue...") 
            input()  # Waits for the user to press Enter
            baseline_statistics = analyze_events(days)
            print("Detecting Anomalies... Done! Press Enter to continue...") 
            input()  # Waits for the user to press Enter
            detect_anomalies(days, baseline_statistics)
        else:
            print("Exiting...")
            break

if __name__ == "__main__":
    main()
