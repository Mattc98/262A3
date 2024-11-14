import sys
import os
import json
import math
import random

LOG_DIR = "logs"

# Data structures to store events and statistics
events = {}
statistics = {}



def read_events(file_path):
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
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)
    
    all_events = []  # List to hold events for all days
    
    for day in range(days):
        log_file = os.path.join(LOG_DIR, f"day_{day + 1}.log")
        daily_events = {"Day": day + 1}  # Dictionary to hold daily events data, including the day number
        
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
        
        # Add daily events to the list of all events
        all_events.append(daily_events)
    
    return all_events

def generate_new_events(days):
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)
    
    all_events = []  # List to hold events for all days
    
    for day in range(days):
        log_file = os.path.join(LOG_DIR, f"new_day_{day + 1}.log")
        daily_events = {"Day": day + 1}  # Dictionary to hold daily events data, including the day number
        
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
        
        # Add daily events to the list of all events
        all_events.append(daily_events)
    
    return all_events

def analyze_stats():
    events = ["Logins", "Time online", "Emails sent", "Emails opened", "Emails deleted"]
    daily_totals = {name: [] for name in events}
    
    log_files = [f for f in os.listdir(LOG_DIR) if f.startswith("day_") and f.endswith(".log")]
    log_files.sort()  # Ensure the files are processed in order

    for log_file in log_files:
        try:
            with open(os.path.join(LOG_DIR, log_file), "r") as file:
                # Load the log file as JSON
                daily_data = json.load(file)

            # Accumulate values for each event
            for event_name, value in daily_data.items():
                if event_name in daily_totals:
                    daily_totals[event_name].append(value)
                elif event_name != "Day":  # Skip the "Day" key
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
        else:
            print(f"No data available for event: {event_name}")

    return baseline_statistics


def detect_anomalies(days, baseline_statistics): 
    """Detect anomalies based on generated events and baseline statistics.""" 
    threshold = 2 * sum(e["weight"] for e in events.values())
    # Calculate the threshold once at the start 
    results = [] # To store results for each day 

    for day in range(days): 
        log_file = os.path.join(LOG_DIR, f"new_day_{day + 1}.log") 
        anomaly_counter = 0 
        try: 
            with open(log_file, "r") as file: 
                daily_data = json.load(file) 

            for event_name, value in daily_data.items(): 
                if event_name in baseline_statistics: 
                    mean = float(baseline_statistics.get(event_name, baseline_statistics[event_name])["mean"]) 
                    std_dev = float(baseline_statistics.get(event_name, baseline_statistics[event_name])["std_dev"]) 

                    deviation = abs(value - mean) / std_dev if std_dev > 0 else 0 
                    weight = events[event_name]["weight"] if event_name in events else 1 
                    anomaly_counter += deviation * weight 
                    
            status = "!!!!!!!!!!!!!!!!!!!!!flagged!!!!!!!!!!!!!!!!!!!!!" if anomaly_counter >= threshold else "okay" 
            results.append({ "day": day + 1, "anomaly_counter": round(anomaly_counter, 2), "threshold": threshold, "status": status })
            with open("log.json", "w") as txt_file:
            	json.dump(results, txt_file, indent=4)
        except (json.JSONDecodeError, FileNotFoundError) as e: 
            print(f"Error reading log file {log_file}: {e}") 
            continue

    return results


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
    events_data = generate_events(days)
    # Print all events outside the function
    for daily_events in events_data:
        print(json.dumps(daily_events, indent=4))
    print("Calculating statistics... Done! Press Enter to continue...") 
    input()  # Waits for the user to press Enter
    baseline_statistics = analyze_stats()  # No days parameter
    print(json.dumps(baseline_statistics, indent=4))

    while True:
        user_input = input("Would you like to load another statistics file (y/n)? ")
        if user_input.lower() == "y":
            new_file = input("Enter new statistics file name: ")
            read_statistics(new_file)  # Correctly read the new statistics file
            days = int(input("Enter number of days to generate events: "))
            
            events_data = generate_new_events(days)
            print("Detecting Anomalies... Done! Press Enter to continue...") 
            input()  # Waits for the user to press Enter
            results = detect_anomalies(days, baseline_statistics)
            # Print the results in JSON format
            print(json.dumps(results, indent=4))
        else:
            print("Exiting...")
            break

if __name__ == "__main__":
    main()

