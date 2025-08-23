# BPO Collections System

This project is a local web application designed for a BPO collections company, facilitating data entry, dispute handling, and data analysis. The application has two main user roles: Team Leaders (TLs) and Data Analysts (DAs).

## Features

- **Data Entry**: Team Leaders can input payment details including campaign, DPD, Loan ID, amount, date paid, operator name, and customer name.
- **Campaign Filtering & Export**: Data Analysts can filter records by campaign and export results to CSV files.
- **Dispute Handling**: Team Leaders can flag records as disputed and enter corrected details. Disputes must be validated before being finalized, and Data Analysts can export validated disputes to a separate CSV.

## Technology Stack

- **Backend**: Flask (Python)
- **Database**: SQLite
- **Frontend**: HTML, CSS, JavaScript
- **Data Handling**: Pandas for CSV export

## Project Structure

```
bpo-collections-system
├── app
│   ├── __init__.py
│   ├── models.py
│   ├── routes
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── team_leader.py
│   │   └── data_analyst.py
│   ├── static
│   │   ├── css
│   │   │   └── main.css
│   │   └── js
│   │       └── main.js
│   ├── templates
│   │   ├── base.html
│   │   ├── login.html
│   │   ├── team_leader
│   │   │   ├── data_entry.html
│   │   │   └── dispute_validation.html
│   │   └── data_analyst
│   │       ├── campaign_filter.html
│   │       └── export.html
│   └── utils
│       ├── __init__.py
│       └── export_helpers.py
├── config.py
├── run.py
├── instance
│   └── collections.db
├── requirements.txt
└── README.md
```

## Setup Instructions

1. Clone the repository:
   ```
   git clone <repository-url>
   cd bpo-collections-system
   ```

2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Run the application:
   ```
   python run.py
   ```

4. Access the application in your web browser at `http://127.0.0.1:5000`.

## Usage

- **Team Leaders** can log in to input payment details and manage disputes.
- **Data Analysts** can log in to filter campaigns and export data.

## License

This project is licensed under the MIT License.