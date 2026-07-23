import re
import pandas as pd

def validate(DATA_FILE, OUTPUT_FILE):
    EXPECTED_COLUMNS = ["Ticket ID", "Category", "Subcategory", "Priority", "Description", "Source"]
    VALID_CATEGORIES = {"Hardware", "Software", "Access", "Security", "Network"}
    VALID_PRIORITIES = {"Low" ,"Medium", "High", "Critical"}
    VALID_SOURCES = {"Public", "Synthetic"}

    EMAIL_RE = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"
    PHONE_RE = r"(\+?\d{1,3}[\s.-]?)?(\(?\d{3}\)?[\s.-]?)\d{3}[\s.-]?\d{4}"
    NAME_RE = r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,2}\b"

    error = []
    warning = []

    df = pd.read_csv(DATA_FILE, dtype=str).fillna("")
    df.columns = df.columns.str.strip()

    for col in df.columns:
        df[col] = df[col].astype(str).str.strip()

    missing_columns = set(EXPECTED_COLUMNS) - set(df.columns)
    if missing_columns:
        error.append(f"Data is missing the column: {missing_columns}")
        print_results(error, warning, OUTPUT_FILE)
        return
    
    required_fields = ["Ticket ID", "Category", "Description", "Source"]
    for col in required_fields:
        missing_rows = df[df[col] == ""]
        if not missing_rows.empty:
            error.append(f"{col} is missing in {missing_rows.index.tolist()}")

    invalid_categories = df[~df["Category"].isin(VALID_CATEGORIES)]
    if not invalid_categories.empty:
        error.append(f"Invalid Categories found: {invalid_categories[['Ticket ID', 'Category']].to_string(index=False)}")
    
    invalid_priorities = df[(df["Priority"] != "") & (~df["Priority"].isin(VALID_PRIORITIES))]
    if not invalid_priorities.empty:
        error.append(f"Invalid priority found: {invalid_priorities[['Ticket ID', 'Priority']].to_string(index=False)}")

    invalid_sources = df[~df["Source"].isin(VALID_SOURCES)]
    if not invalid_sources.empty:
        error.append(f"Invalid source found: {invalid_sources[['Ticket ID', 'Source']].to_string(index=False)}")
    
    duplicate_ids = df[df["Ticket ID"].duplicated(keep=False)]
    if not duplicate_ids.empty:
        error.append(f"Duplicate ticket id found: {duplicate_ids[['Ticket ID', 'Category', 'Description']].to_string(index=False)}")

    text = df["Subcategory"] + " " + df["Description"]

    possible_emails = df[text.str.contains(EMAIL_RE, regex=True, case=False)]
    if not possible_emails.empty:
        warning.append(f"Possible email found: {possible_emails[['Ticket ID', 'Subcategory', 'Description']].to_string(index=False)}")

    possible_phone = df[text.str.contains(PHONE_RE, regex=True, case=False)]
    if not possible_phone.empty:
        warning.append(f"Possible phone number found: {possible_phone[['Ticket ID', 'Subcategory', 'Description']].to_string(index=False)}")
    
    possible_name = df[text.str.contains(NAME_RE, regex=True, case=True)]
    if not possible_name.empty:
        warning.append(f"Possible name found: {possible_name[['Ticket ID', 'Subcategory', 'Description']].to_string(index=False)}")

    print_results(error, warning, OUTPUT_FILE)

def print_results(errors, warnings, OUTPUT_FILE):
    with open(OUTPUT_FILE, "w") as file:
        file.write("")
        file.write("Validation Results\n")
        if errors:
            file.write("Errors:-\n")
            for error in errors:
                file.write(error)
                file.write("\n")
        else:
            file.write("No errors found\n")
        
        if warnings:
            file.write("Warnings:-\n")
            for warning in warnings:
                file.write(warning)
                file.write("\n")
        else:
            file.write("No warnings found")

if __name__ == "__main__":
    validate(
        DATA_FILE = "combined_ticket.csv",
        OUTPUT_FILE = "validation_output.txt"
    )