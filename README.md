# FinTrack - Your Personal Financial Management System

## Overview

Welcome to FinTrack, a user-friendly, Python-based financial management application designed to help you organize and track your finances effectively.  FinTrack uses a robust SQLite database to store your financial data locally, ensuring that you have full control and easy access. It offers features ranging from basic transaction recording to advanced reporting, fixed asset management, recurring transactions, and even cloud synchronization.

This README provides a comprehensive guide to understanding and using FinTrack, covering all its functionalities and features.

## Installation Nuitka:
python -m nuitka --onefile --windows-disable-console --windows-icon-from-ico="C:\Users\Niino\Desktop\Accounting_System\data\base.ico" --include-data-dir=data=data --follow-imports --enable-plugin=pyside6 main.py
## Table of Contents

1.  [Features](#features)
2.  [Getting Started](#getting-started)
    *   [Installation](#installation)
    *   [Database Initialization](#database-initialization)
    *   [Running FinTrack](#running-fintrack)
3.  [Functionality Breakdown](#functionality-breakdown)
    *   [Setup Menu](#setup-menu)
        *   [Accounts](#accounts)
        *   [Accounting Periods](#accounting-periods)
        *   [Categories](#categories)
    *   [Transactions Menu](#transactions-menu)
        *   [Add Transaction](#add-transaction)
        *   [Add Transaction from Template](#add-transaction-from-template)
        *   [View Transactions](#view-transactions)
        *   [Edit Transaction](#edit-transaction)
        *   [Delete Transaction](#delete-transaction)
    *   [Templates Menu](#templates-menu)
        *   [Create Template](#create-template)
        *   [View Templates](#view-templates)
        *   [Edit Template](#edit-template)
        *   [Delete Template](#delete-template)
    *   [Recurring Transactions Menu](#recurring-transactions-menu)
        *   [Create Recurring Transaction](#create-recurring-transaction)
        *   [Create Transaction from Template](#create-recurring-transaction-from-template-1)
        *   [Edit Recurring Transaction](#edit-recurring-transaction)
        *   [Delete Recurring Transaction](#delete-recurring-transaction)
    *   [AR/AP Menu (Accounts Receivable/Accounts Payable)](#arap-menu)
        *   [View Outstanding Balances](#view-outstanding-balances)
        *   [Debtor/Creditor Management](#debtorcreditor-management)
            *   [New Debtor/Creditor](#new-debtorcreditor)
            *   [Edit Debtor/Creditor](#edit-debtorcreditor)
            *   [Delete Debtor/Creditor](#delete-debtorcreditor)
        *   [Debtor Transactions](#debtor-transactions)
            *   [Register Asset Transfer (Outflow)](#register-asset-transfer-outflow)
            *   [Record Asset Recovery (Inflow)](#record-asset-recovery-inflow)
            *   [Adjust Receivable](#adjust-receivable)
            *   [Write-Off Receivable](#write-off-receivable)
        *   [Creditor Transactions](#creditor-transactions)
            *   [Register Asset Transfer (Inflow)](#register-asset-transfer-inflow)
            *   [Record Liability Settlement (Outflow)](#record-liability-settlement-outflow)
            *   [Adjust Payable](#adjust-payable)
            *   [Cancel Payable](#cancel-payable)
        *   [AR/AP Settings](#arap-settings)
    *   [Fixed Assets Menu](#fixed-assets-menu)
        *   [Register Purchased Asset](#register-purchased-asset)
            *   [Single Account Purchase](#single-account-purchase)
            *   [Multiple Accounts Purchase](#multiple-accounts-purchase)
        *   [Register Pre-Existing Asset](#register-pre-existing-asset)
        *   [Calculate Depreciation](#calculate-depreciation)
        *   [Purge Asset Records](#purge-asset-records)
        *   [Fixed Assets Settings](#fixed-assets-settings)
    *   [Reports Menu](#reports-menu)
        *   [Income Statement](#income-statement)
        *   [Balance Sheet](#balance-sheet)
        *   [Cash Flow](#cash-flow)
            *   [Actual Cash Flow](#actual-cash-flow)
            *   [Cash Flow Settings](#cash-flow-settings)
    *   [Sync Menu](#sync-menu)
        *   [Upload Data to Drive](#upload-data-to-drive)
        *   [Download Data from Drive](#download-data-from-drive)
        *   [Check Sync Status](#check-sync-status)
        *   [Sync Settings](#sync-settings)
    *   [Help Menu](#help-menu)
4.  [Backup System](#backup-system)
5.  [Database Structure](#database-structure)
6.  [Troubleshooting](#troubleshooting)
7.  [Contributing](#contributing)
8.  [License](#license)
9. [Contact](#contact)

## 1. Features

FinTrack offers a comprehensive suite of features to manage your financial data:

*   **Database Management:** Uses a local SQLite database for secure and reliable data storage.
*   **Account Management:** Create, view, edit, and delete financial accounts. Categorize accounts by type (Asset, Liability, Equity, Revenue, Expense).
*   **Category Management:**  Define categories to group accounts for reporting and analysis.
*   **Transaction Recording:** Record financial transactions with details like date, description, debited and credited accounts, and amount.
*   **Transaction Templates:** Create reusable templates for frequent transactions, saving you time and effort.
*   **Recurring Transactions:** Automate the recording of transactions that happen regularly (daily, weekly, monthly, yearly, or custom intervals).
*   **Accounts Receivable & Payable (AR/AP):**  Manage debtors and creditors, track outstanding balances, and handle AR/AP transactions.
*   **Fixed Asset Management:**
    *   Register fixed assets (e.g., equipment, machinery).
    *   Calculate depreciation using various methods (Straight-Line, Sum of the Years' Digit, Declining Balance, Double-Declining Balance, Units of Production).
    *   Generate depreciation schedules.
    *   Track asset purchases, disposals, and book values.
*   **Financial Reporting:** Generate essential financial reports:
    *   **Income Statement (Profit & Loss):**  Shows your financial performance over a specific period.
    *   **Balance Sheet:**  Provides a snapshot of your assets, liabilities, and equity at a specific point in time.
    *   **Cash Flow Statement:**  Tracks the movement of cash into and out of your accounts.
*   **Future Transaction Processing:** Automatically processes scheduled future transactions (e.g., from recurring transactions) on their due dates.
*   **Google Drive Synchronization:** Back up and synchronize your data with Google Drive (optional, requires additional libraries and a Google Cloud service account).
*   **Automatic Backup:** Creates a backup of your database every time you close the application.
*   **User-Friendly Interface:** Designed with a clear and intuitive graphical user interface (GUI) using PySide6.

## 2. Getting Started

### 2.1 Installation

1.  **Python:** Ensure you have Python 3.6 or later installed on your system.
2.  **Download FinTrack:** Download the FinTrack application files (the `.py` files). Place them in a single directory.
3.  **Install PySide6:**  FinTrack uses the PySide6 library for its graphical user interface. Install it using pip:

    ```bash
    pip install PySide6
    ```
4. **Google Drive Sync (Optional):**

   *   **Install Libraries:**
      ```bash
      pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib
      ```
   * **Credentials:**

      1.  **Create a Project in Google Cloud Console:** Go to [Google Cloud Console](https://console.cloud.google.com/) and create a new project.

      2.  **Enable the Google Drive API:**  In your project, go to "APIs & Services" -> "Enabled APIs & services", click "+ ENABLE APIS AND SERVICES", search for "Google Drive API", and enable it.

      3.  **Create Service Account Credentials:**
          *   Go to "APIs & Services" -> "Credentials".
          *   Click "+ CREATE CREDENTIALS" and select "Service account".
          *   Fill in the service account details.  You can name it something like "FinTrack Service Account".
          *   Grant the service account the "Editor" role (for simplicity, but be aware of the permissions granted).  In a production environment, you should use a more restricted role.
          *   Click "DONE".
          *   Click on the newly created service account.
          *   Go to the "KEYS" tab.
          *   Click "ADD KEY" -> "Create new key".
          *   Select "JSON" as the key type and click "CREATE".
          *   This will download a JSON file (e.g., `credentials.json`). **Save this file securely, as it grants access to your Google Drive.**

      4.  **Place Credentials File:**  Place the downloaded `credentials.json` file in a `credentials` directory *inside* the FinTrack application directory. The expected path is `[FinTrack directory]/credentials/credentials.json`. The application looks for the credentials file in this specific location.

      5. **Google Drive Folder ID:** You'll need a Google Drive folder ID for FinTrack to sync with.
         * Go to your Google Drive.
         * Create a new folder (or use an existing one) where you want FinTrack to store its data.
         * Open this folder.
         * The folder ID is the part of the URL after `folders/`. For example, if the URL is `https://drive.google.com/drive/folders/1ZqSLWL7POqp0gufYuMxFdyHX0sjDKMtJ`, the folder ID is `1ZqSLWL7POqp0gufYuMxFdyHX0sjDKMtJ`. You'll need this ID later in the Sync Settings.

### 2.2 Database Initialization

FinTrack automatically initializes the database the first time you run it.  No manual steps are required.  The database file (`financial_system.db`) will be created in a `data` subdirectory within the FinTrack application folder.  The application also pre-populates the database with some default account types.

### 2.3 Running FinTrack

1.  Open a terminal or command prompt.
2.  Navigate to the directory where you placed the FinTrack Python files.
3.  Run the `main.py` file:

    ```bash
    python main.py
    ```

This will launch the FinTrack application window.

## 3. Functionality Breakdown

FinTrack's main window has a menu bar at the top, organizing its functionality.  Each menu item is explained below:

### 3.1 Setup Menu

The **Setup** menu is for configuring the core elements of your financial tracking system.

#### 3.1.1 Accounts

*   **Create Account:**
    *   **Code:** A unique code for the account (e.g., 1000 for Cash).
    *   **Name:** The account's name (e.g., "Checking Account").
    *   **Type:**  Select from: Current Asset, Fixed Asset, Current Liability, Long-term Liability, Equity, Revenue, Expense.
    *   **Category:** (Optional) Assign a category for reporting.
    *   **Description:** (Optional) Add a description.
    *   **Is Active:**  Check to make the account active.
    *   Click **Save**.

*   **View Accounts:** Displays a table of all your accounts, with their code, name, type, and balance.

*   **Update Account:**
    1.  Click **Search** to find the account to edit.
    2.  Modify the fields as needed.
    3.  Click **Save**.

*   **Delete Account:**
    1.  Click **Search** to find the account to delete.
    2.  **Important:** Confirm the deletion.  Deleting an account is irreversible and will affect any transactions associated with it.

#### 3.1.2 Accounting Periods

*   **Create Accounting Periods:**
    *   **Start Date:**  Select the start date of the period.
    *   **End Date:** Select the end date of the period.
    * **Status** Open/Close.
    *   Click **Save**.

*   **View Accounting Periods:** Displays a table of all defined accounting periods.

*   **Update Accounting Periods:**
    1.  Click **Search** to find the period to edit.
    2.  Modify the fields as needed.
    3.  Click **Save**.

*   **Delete Accounting Periods:**
    1.  Click **Search** to find the period to delete.
    2.  **Important:** Confirm the deletion.

#### 3.1.3 Categories

*   **Create Category:**
    *   **Name:** Enter a name for the category (e.g., "Office Supplies").
    *   **Description:** (Optional) Add a description.
    *   Click **Save**.

*   **View Categories:** Displays a table of all defined categories.

*   **Update Category:**
    1.  Click **Search** to find the category to edit.
    2.  Modify the name or description.
    3.  Click **Save**.

*   **Delete Category:**
    1.  Click **Search** to find the category to delete.
    2.  **Important:** Confirm the deletion.

### 3.2 Transactions Menu

*   **Add Transaction:**
    *   **Date:** Select the transaction date.
    *   **Description:** Enter a description for the transaction.
    *   **Debited Account:** Click **Search** to choose the account to debit.
    *   **Credited Account:** Click **Search** to choose the account to credit.
    *   **Amount:** Enter the transaction amount.
    *   Click **Save**.

*   **Add Transaction from Template:**
    1.  Select a template from the list displayed.
    2.  *(Optional)* View template details by clicking the "View Details" button on a selected template.
    3.  Click **Ok** to proceed with the selected template.
    4. A window that allows you to modify the amounts of the transactions will be displayed.
    5. Select date and create transactions.

*   **View Transactions:** Displays a table of all your recorded transactions.

*   **Edit Transaction:**
    1.  Click **Search** to find the transaction to edit.
    2.  Modify the fields as needed.  The balances of the affected accounts will be automatically updated.
    3.  Click **Save**.

*   **Delete Transaction:**
    1.  Click **Search** to find the transaction to delete.
    2.  **Important:** Confirm the deletion.  This will reverse the transaction's effect on account balances.

### 3.3 Templates Menu

*   **Create Template:**
    1.  **Template Name:** Enter a name for the template.
    2.  Click **Add Transaction** to add a transaction line to the template.
        *   **Description:** Enter a description for this transaction line.
        *   **Debited Account:** Click **Search** to choose the account to debit.
        *   **Credited Account:** Click **Search** to choose the account to credit.
        *   **Amount:** Enter the amount.
        *   Click **Ok** to add the transaction line.
    3.  Repeat step 2 for each transaction line in the template.
    4. Click **Save** to create the template.

*   **View Templates:** Displays a table of all your templates.  Double-clicking a template shows its details.

*   **Edit Template:**
    1.  Click **Search** to find the template to edit.
    2.  Modify the template name or add, edit, or delete transaction lines (as in "Create Template").
    3.  Click **Save**.

*   **Delete Template:**
    1.  Click **Search** to find the template to delete.
    2.  **Important:** Confirm the deletion.  This will also delete all associated transaction lines within the template.

### 3.4 Recurring Transactions Menu

*   **Create Recurring Transaction:**
    *   **Description:** Enter a description.
    *   **Debited Account:** Click **Select** to choose the account to debit.
    *   **Credited Account:** Click **Select** to choose the account to credit.
    *   **Amount:** Enter the amount.
    *   **Frequency:** Select "daily", "weekly", "monthly", "yearly", or "days" (for a custom interval).
    *   If you select "days," enter the interval in days in the **Interval (days):** field.
    *   **Start Date:** Select the start date.
    *   **End Date:** Select an end date, or choose "No End Date".
    *   Click **Confirm**.  This creates the recurring transaction and schedules all future transactions up to 70 years in the future.

* **Create Recurring Transaction from Template:**

   1.  **Template:** Click "Select Template" and choose a predefined template.
   2.  Review the "Transactions Preview Table," which displays the transaction details from the selected template.
   3.  **Frequency:** Select how often the transaction should occur (daily, weekly, monthly, yearly, or a custom number of days).
   4.  If you select "days" for the frequency, enter the number of days in the "Interval (days):" field.
   5.  **Start Date:** Click "Select Date" to choose the starting date for the recurring transaction.
   6.  **End Date:**
      *   Choose "No End Date" for an ongoing recurring transaction.
      *   Select "Select End Date" and click "Select Date" to specify an end date.
   7.  Click **Confirm** to create the recurring transaction and the associated future transactions.

*   **Edit Recurring Transaction:**
    1.  Click **Select Recurring Transaction** to find the transaction to edit.
    2.  Modify the fields as needed.  Changes will affect future scheduled transactions.
    3.  Click **Confirm Edit**.

*   **Delete Recurring Transaction:**
    1.  Click **Select Recurring Transaction** to find the transaction to delete.
    2.  **Important:** Confirm the deletion.  This will also delete all associated future transactions that haven't yet been processed.

### 3.5 AR/AP Menu

*   **View Outstanding Balances:** Displays two tables: one for Debtors (people who owe you money) and one for Creditors (people you owe money to).  Double-click on a debtor/creditor to view their transaction history.

*   **Debtor/Creditor Management:**

    *   **New Debtor/Creditor:**
        *   **Name:** Enter the name.
        *   Select either **Debtor** or **Creditor**.
        *   Click **Save**.

    *   **Edit Debtor/Creditor:**
        1.  Click **Select Debtor/Creditor** to find the record to edit.
        2.  Modify the name.
        3.  Click **Edit**.

    *   **Delete Debtor/Creditor:**
        1.  Click **Select Debtor/Creditor** to find the record to delete.
        2.  **Important:** Confirm the deletion.

*   **Debtor Transactions:**

    *   **Register Asset Transfer (Outflow):**  Records a transaction where you provide goods or services to a debtor (increasing the receivable).
        1.  **Date:** Select the date.
        2.  **Debtor:** Select the debtor.
        3.  **Asset:** Select the asset (e.g., service provided, goods sold) that is being transferred.
        4.  **Details:** (Optional) Enter a description.
        5.  **Amount:** Enter the amount.
        6.  Click **Register**.

    *   **Record Asset Recovery (Inflow):** Records a payment received from a debtor (decreasing the receivable).
        1.  **Date:** Select the date.
        2.  **Debtor:** Select the debtor.
        3.  **Asset:** Select the asset (e.g., cash, bank account) received.
        4.  **Details:** (Optional) Enter a description.
        5.  **Amount:** Enter the amount.
        6.  Click **Record**.

    *   **Adjust Receivable:**  Modifies the amount of an existing receivable transaction.
        1.  **Debtor:** Select the debtor.
        2.  **Transaction:** Select the transaction to adjust.
        3.  **Details:** Update the details (if needed).
        4.  **Amount:** Enter the *new* amount.
        5.  Click **Adjust**.

    *   **Write-Off Receivable:**  Removes an uncollectible receivable.
        1.  **Debtor:** Select the debtor.
        2.  **Transaction:** Select the transaction to write off.
        3.  **Important:** Confirm the write-off.

*   **Creditor Transactions:**

    *   **Register Asset Transfer (Inflow):**  Records a transaction where you receive goods or services from a creditor (increasing the payable).
        1.  **Date:** Select the date.
        2.  **Creditor:** Select the creditor.
        3.  **Asset:** Select the asset (e.g., goods received, services rendered).
        4.  **Details:** (Optional) Enter a description.
        5.  **Amount:** Enter the amount.
        6.  Click **Register**.

    *   **Record Liability Settlement (Outflow):** Records a payment made to a creditor (decreasing the payable).
        1.  **Date:** Select the date.
        2.  **Creditor:** Select the creditor.
        3.  **Asset (Payment):** Select the asset (e.g., cash, bank account) used for payment.
        4.  **Details:** (Optional) Enter a description.
        5.  **Amount:** Enter the amount.
        6.  Click **Record Settlement**.

    *   **Adjust Payable:** Modifies the amount of an existing payable transaction.
        1.  **Creditor:** Select the creditor.
        2.  **Transaction:** Select the transaction to adjust.
        3.  **Details:** Update the details (if needed).
        4.  **Amount:** Enter the *new* amount.
        5.  Click **Adjust**.

    *   **Cancel Payable:**  Removes a payable transaction (e.g., if goods are returned).
        1.  **Creditor:** Select the creditor.
        2.  **Transaction:** Select the transaction to cancel.
        3.  **Important:** Confirm the cancellation.

*   **AR/AP Settings:**  Allows you to set the default Accounts Receivable and Accounts Payable accounts used by FinTrack.

### 3.6 Fixed Assets Menu

*   **Register Purchased Asset:**

    *   **Single Account Purchase:**
        1.  **Asset Name:** Enter the asset's name.
        2.  **Asset Code:**  Enter a unique code for the asset.
        3.  **Purchase Date:** Select the date the asset was purchased.
        4.  **Original Cost:** Enter the original cost of the asset.
        5.  **Salvage Value:** Enter the estimated salvage value of the asset.
        6.  **Depreciation Method:** Choose a depreciation method (Straight-Line, Sum of the Years' Digit, Declining Balance, Double-Declining Balance, Units of Production).
        7.  Fill in the required fields based on the selected depreciation method (Useful Life, Depreciation Rate, or Total Estimated Units).
        8.  **Payment Account:**  Select the account used to pay for the asset.
        9.  Click **Register Purchase**.

    *   **Multiple Accounts Purchase:**  Similar to Single Account Purchase, but allows you to specify multiple accounts for payment.  Use the "Add Payment Account" button to add each account and the corresponding amount.  The total of the payment amounts must equal the original cost.

*   **Register Pre-Existing Asset:**  For assets you already owned before using FinTrack.
    1.  **Asset Name:** Enter the asset's name.
    2.  **Asset Code:** Enter a unique code.
    3.  **Purchase Date:** Select the *original* purchase date.
    4.  **Original Cost:** Enter the original cost.
    5.  **Salvage Value:** Enter the salvage value.
    6.  **Depreciation Method:** Select the method.
    7.  Fill in the required fields based on the selected method.
    8.  **Accounting Period:** Select the accounting period during which you are importing the asset. FinTrack will calculate accumulated depreciation up to the *start* of this period.
    9.  Click **Import Asset**.

*   **Calculate Depreciation:**
    1.  **Select Asset:** Click "Select Asset" and choose the asset from the list.
    2.  **Calculate Depreciation Up To:** Select the date up to which you want to calculate depreciation.
    3.  Click **Calculate and Schedule Depreciation**. This will calculate depreciation for the asset, create entries in the `depreciation_schedule` table, and schedule future depreciation transactions.

*   **Purge Asset Records:**
    1.  Click **Select Asset**.
    2.  **Important:**  This will permanently delete ALL data related to the selected asset (transactions, depreciation schedule, and the asset record itself).  This is irreversible.

*   **Fixed Assets Settings:**  Allows you to set:
    *   **Owner's Equity Account:** The default account used when registering a pre-existing asset.
    *   **Depreciation Expense Account:** The default account used for recording depreciation expense.

### 3.7 Reports Menu

*   **Income Statement:**  Generates an income statement for a selected accounting period.  Select the period, and the report will show revenues, expenses, and the resulting net income or loss.

*   **Balance Sheet:** Generates a balance sheet as of the end date of a selected accounting period.  It displays assets, liabilities, and equity.

*   **Cash Flow:**

    *   **Actual Cash Flow:** Generates a cash flow statement for a selected accounting period.  You must configure your "cash accounts" in the Cash Flow Settings for this report to be accurate.

    *   **Cash Flow Settings:**  Opens a window where you can select which accounts are considered "cash accounts" for the purpose of generating the Cash Flow Statement. This usually includes accounts like checking, savings, and petty cash.

### 3.8 Sync Menu

The **Sync** menu provides options for synchronizing your data with Google Drive.  **Important:** This requires the Google API libraries and a properly configured Google Cloud service account (see [Installation](#installation)).

*   **Upload Data to Drive:**  Uploads your local FinTrack data files to your Google Drive folder.

*   **Download Data from Drive:** Downloads the data files from your Google Drive folder to your local FinTrack `data` directory.

*   **Check Sync Status:**  Compares your local files with the files in your Google Drive folder and shows any differences (files to upload, files to download, or files that are in sync).

*   **Sync Settings:**  Opens a dialog to configure synchronization settings:
    *   **Google Drive Settings:**
        *   **Folder ID:** Enter the ID of your Google Drive folder.
        *   **Credentials File:** Enter the full path to your `credentials.json` file (or click **Browse...** to select it).  This is the JSON key file you downloaded from the Google Cloud Console.
        *   **Local Directory:**  Enter the path to your local FinTrack `data` directory (usually just `data`).

    *   **Legacy Server Settings:**  These settings are not currently used but are included for potential future expansion.
        *   **Server URL:**
        *   **Username:**
        *   **API Key:**

    *   **Synchronization Options:**
        *   **Auto-Sync:** Check to enable automatic synchronization.
        *   **Sync Interval:** Select the frequency for automatic synchronization.
        *   **Conflict Resolution:** Choose how to handle conflicts (if the same file is modified both locally and on Drive): "Always ask," "Remote wins," or "Local wins."

    Click **Save** to save your settings.

### 3.9 Help Menu

The Help menu is currently a placeholder.  It can be extended to include application documentation, an "About" dialog, or links to support resources.

## 4. Backup System

FinTrack has a built-in automatic backup system:

*   **Automatic Backups:**  Every time you *close* the FinTrack application, a backup is created.
*   **Backup Format:** The backup is a ZIP file containing all the files in the `data` directory (including the `financial_system.db` database file).
*   **Backup Location:** Backups are saved in a `backups` directory located in the same directory as the FinTrack application.
*   **Filename:** Backup files are named with the format `fintrack_backup_YYYYMMDD_HHMMSS.zip`, where `YYYYMMDD_HHMMSS` is the timestamp of the backup.
*   **Backup Rotation:** FinTrack keeps the 20 most recent backups.  Older backups are automatically deleted.

## 5. Database Structure

FinTrack uses an SQLite database (`financial_system.db`) with the following tables:

| Table Name                       | Description                                                                          |
| :------------------------------- | :----------------------------------------------------------------------------------- |
| `account_types`                  | Stores account types (Asset, Liability, Equity, Revenue, Expense).                   |
| `categories`                     | Stores categories for grouping accounts.                                             |
| `accounts`                       | Stores all financial accounts, including their current balance.                     |
| `accounting_periods`            | Stores defined accounting periods (start and end dates).                               |
| `debtor_creditor`                | Stores information about debtors and creditors.                                    |
| `debtor_creditor_transactions` | Records transactions specifically related to debtors and creditors.                  |
| `fixed_assets`                   | Stores details of fixed assets.                                                      |
| `depreciation_schedule`          | Stores the calculated depreciation schedule for each fixed asset.                      |
| `transactions`                   | Stores all financial transactions.                                                 |
| `future_transactions`            | Stores scheduled future transactions (generated by recurring transactions).        |
| `transaction_templates`          | Stores the main definition of transaction templates.                                 |
| `template_transactions`          | Stores individual transactions within a template.                                     |
| `template_transaction_details`   | Stores the debit/credit details for each transaction within a template.                |
| `recurring_transactions`         | Stores the definitions for recurring transactions.                                   |

## 6. Troubleshooting

*   **"ModuleNotFoundError: No module named 'PySide6'" (or similar):**  You need to install the required libraries.  See the [Installation](#installation) section.
*   **Database Errors:**  If you encounter database errors, ensure that the application has read/write access to the `data` directory and the `financial_system.db` file.  Try restarting the application.  If the problem persists, you may need to restore from a backup.
*   **Google Drive Sync Issues:**
    *   Make sure you have installed the required Google API libraries.
    *   Verify that your `credentials.json` file is correctly placed in the `credentials` directory.
    *   Ensure you have entered the correct Google Drive Folder ID in the Sync Settings.
    *   Check your internet connection.
* **Credentials.json not found** Ensure that credentials.json is in the credentials file.
## 7. Contributing

If you're interested in contributing to FinTrack, feel free to fork the repository and submit pull requests.  Areas for potential contributions include:

*   Adding new report types.
*   Improving the Google Drive synchronization logic.
*   Adding support for other cloud storage services.
*   Enhancing the user interface.
*   Implementing more advanced financial analysis features.
*   Adding localization support (translation to other languages).
*   Writing unit tests.

## 8. License

This project is open-source (Specify License here, e.g., MIT License, GPL, etc.). Please add a `LICENSE` file.

## 9. Contact

[Your Name/Organization Name]
[Your Email Address]

---

This README provides a detailed overview of FinTrack. Remember to keep this document updated as you add new features or make changes to the application.  Good documentation is crucial for any project!