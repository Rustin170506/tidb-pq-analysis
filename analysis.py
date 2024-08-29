import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Constants
# Minimum difference in priority to consider as significant
PRIORITY_DIFFERENCE_THRESHOLD = 0.05

# Ratio of table sizes to consider one table as significantly larger than another
TABLE_SIZE_RATIO_THRESHOLD = 2

# Number of days after which a table is considered potentially starved
STARVATION_THRESHOLD_DAYS = 2

# Quantile threshold for considering a change ratio as high
CHANGE_RATIO_QUANTILE = 0.75

# Thresholds for reporting issues
LARGE_BLOCKING_SMALL_THRESHOLD = 10  # Number of instances to report large tables blocking small ones
SMALL_BLOCKING_LARGE_THRESHOLD = 10  # Number of instances to report small tables blocking large ones
STARVED_TABLES_THRESHOLD = 5  # Number of instances to report potentially starved tables
HIGH_CHANGE_LOW_PRIORITY_THRESHOLD = 5  # Number of instances to report high change but low priority tables

# Conversion factor from days to seconds
SECONDS_PER_DAY = 24 * 3600

def load_data(file_path: str) -> pd.DataFrame:
    """
    Load CSV data and preserve the original order.

    Args:
        file_path (str): Path to the CSV file.

    Returns:
        pd.DataFrame: Loaded data as a pandas DataFrame.
    """
    return pd.read_csv(file_path)

def detect_priority_issues(df: pd.DataFrame) -> tuple:
    """
    Analyze the priority formula for potential issues.

    Args:
        df (pd.DataFrame): Input DataFrame containing table data.

    Returns:
        tuple: Contains lists of different types of issues detected.
    """
    issues = []
    large_blocking_small = []
    small_blocking_large = []
    starved_tables = []
    high_change_low_priority = []

    for i in range(len(df) - 1):
        current, next_table = df.iloc[i], df.iloc[i+1]

        # Detect large tables potentially blocking small tables
        if current['TableSize'] > next_table['TableSize'] * TABLE_SIZE_RATIO_THRESHOLD and current['CalculatedPriority'] - next_table['CalculatedPriority'] > PRIORITY_DIFFERENCE_THRESHOLD:
            large_blocking_small.append((current['ID'], next_table['ID'], current['TableSize'], next_table['TableSize']))

        # Detect small tables potentially blocking large tables
        if current['TableSize'] * TABLE_SIZE_RATIO_THRESHOLD < next_table['TableSize'] and current['CalculatedPriority'] - next_table['CalculatedPriority'] > PRIORITY_DIFFERENCE_THRESHOLD:
            small_blocking_large.append((current['ID'], next_table['ID'], current['TableSize'], next_table['TableSize']))

        # Detect potential table starvation
        if current['TimeSinceLastAnalyze'] > STARVATION_THRESHOLD_DAYS * SECONDS_PER_DAY and current['CalculatedPriority'] < df['CalculatedPriority'].median():
            starved_tables.append((current['ID'], current['TimeSinceLastAnalyze'], current['CalculatedPriority']))

        # Detect tables with high change ratio but low priority
        if current['ChangeRatio'] > df['ChangeRatio'].quantile(CHANGE_RATIO_QUANTILE) and current['CalculatedPriority'] < df['CalculatedPriority'].median():
            high_change_low_priority.append((current['ID'], current['ChangeRatio'], current['CalculatedPriority']))

    # Summarize issues if they exceed thresholds
    if len(large_blocking_small) > LARGE_BLOCKING_SMALL_THRESHOLD:
        issues.append(f"Found {len(large_blocking_small)} instances where larger tables may be blocking smaller tables")

    if len(small_blocking_large) > SMALL_BLOCKING_LARGE_THRESHOLD:
        issues.append(f"Found {len(small_blocking_large)} instances where smaller tables may be blocking larger tables")

    if len(starved_tables) > STARVED_TABLES_THRESHOLD:
        issues.append(f"Found {len(starved_tables)} instances of potential table starvation")

    if len(high_change_low_priority) > HIGH_CHANGE_LOW_PRIORITY_THRESHOLD:
        issues.append(f"Found {len(high_change_low_priority)} instances of tables with high change ratio but low priority")

    return issues, large_blocking_small, small_blocking_large, starved_tables, high_change_low_priority

def create_priority_visualizations(df: pd.DataFrame):
    """
    Create visualizations to help understand the relationships between variables and priority.

    Args:
        df (pd.DataFrame): Input DataFrame containing table data.
    """
    fig, axs = plt.subplots(1, 3, figsize=(18, 6))

    axs[0].scatter(df['ChangeRatio'], df['CalculatedPriority'])
    axs[0].set_xlabel('Change Ratio')
    axs[0].set_ylabel('Calculated Priority')
    axs[0].set_title('Priority vs Change Ratio')

    axs[1].scatter(df['TableSize'], df['CalculatedPriority'])
    axs[1].set_xlabel('Table Size')
    axs[1].set_ylabel('Calculated Priority')
    axs[1].set_title('Priority vs Table Size')
    axs[1].set_xscale('log')  # Use log scale for better visualization of table size

    axs[2].scatter(df['TimeSinceLastAnalyze'], df['CalculatedPriority'])
    axs[2].set_xlabel('Time since last analyze (seconds)')
    axs[2].set_ylabel('Calculated Priority')
    axs[2].set_title('Priority vs Time Since Last Analyze')

    plt.tight_layout()
    plt.savefig('priority_relationships.png')
    plt.close()

def analyze_priority_formula(df: pd.DataFrame):
    """
    Perform a comprehensive analysis of the priority formula and its effects.

    Args:
        df (pd.DataFrame): Input DataFrame containing table data.
    """
    issues, large_blocking_small, small_blocking_large, starved_tables, high_change_low_priority = detect_priority_issues(df)

    # Report potential issues
    if issues:
        print("Potential issues with the priority formula:")
        for issue in issues:
            print(f"- {issue}")
    else:
        print("No significant issues found with the priority formula.")

    # Report specific instances of issues (limited to first 5 for brevity)
    issue_types = [
        ("Larger tables potentially blocking smaller tables", large_blocking_small),
        ("Smaller tables potentially blocking larger tables", small_blocking_large),
        ("Potential table starvation", starved_tables),
        ("Tables with high change ratio but low priority", high_change_low_priority)
    ]

    for issue_name, issue_list in issue_types:
        if issue_list:
            print(f"\n{issue_name}:")
            for instance in issue_list[:5]:
                if issue_name.startswith("Larger") or issue_name.startswith("Smaller"):
                    print(f"Table {instance[0]} (size {instance[2]}) may block table {instance[1]} (size {instance[3]})")
                elif issue_name.startswith("Potential table starvation"):
                    print(f"Table {instance[0]} (last analyzed {instance[1]} seconds ago) has low priority {instance[2]:.4f}")
                else:
                    print(f"Table {instance[0]} (change ratio {instance[1]:.2f}) has low priority {instance[2]:.4f}")
            if len(issue_list) > 5:
                print(f"... and {len(issue_list) - 5} more instances.")

    # Create and save visualizations
    create_priority_visualizations(df)
    print("\nVisualization of priority relationships saved as 'priority_relationships.png'")

    # Calculate and report additional statistics
    print("\nCorrelation Statistics:")
    print(f"Change Ratio vs Priority: {df['ChangeRatio'].corr(df['CalculatedPriority']):.4f}")
    print(f"Table Size vs Priority: {df['TableSize'].corr(df['CalculatedPriority']):.4f}")
    print(f"Time Since Last Analyze vs Priority: {df['TimeSinceLastAnalyze'].corr(df['CalculatedPriority']):.4f}")

def main():
    """
    Main function to orchestrate the analysis process:
    load data, analyze formula, and visualize relationships.
    """
    csv_file = 'calculated_priorities.csv'
    df = load_data(csv_file)
    analyze_priority_formula(df)

if __name__ == "__main__":
    main()
