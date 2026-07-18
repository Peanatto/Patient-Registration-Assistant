#!/usr/bin/env python3
import sys
import gspread

def main() -> int:
    sheet_name = "patient-registration-assistant-records"
    
    try:
        # Authenticate using the service account file in the current directory
        print("Authenticating with service_account.json...")
        gc = gspread.service_account(filename="service_account.json")
        
        # Open the target Google Sheet
        spreadsheet = gc.open(sheet_name)
        worksheet = spreadsheet.sheet1
        
        # Fetch all values to check headers and row count
        all_values = worksheet.get_all_values()
        
        print(f"\nConnected to: {spreadsheet.title}")
        
        if all_values:
            header_row = all_values[0]
            # Data rows exclude the header row
            data_row_count = len(all_values) - 1
            print(f"Header row: {header_row}")
            print(f"Row count (data only): {data_row_count}")
        else:
            print("Header row: []")
            print("Row count (data only): 0")
            
        print("Connection OK.")
        return 0

    except gspread.exceptions.SpreadsheetNotFound:
        print(f"\nError: Could not find spreadsheet named '{sheet_name}'.", file=sys.stderr)
        print("Make sure the sheet exists and is shared with your service account's client_email as an Editor.", file=sys.stderr)
        return 1
    except FileNotFoundError:
        print("\nError: 'service_account.json' not found in the current directory.", file=sys.stderr)
        print("Make sure you moved your downloaded key file into the project root and renamed it.", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"\nConnection Failed: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())