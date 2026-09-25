# GitHub Technology Trends Data Platform

An end-to-end data engineering project that collects repository data from the **GitHub API**, processes and cleans the data through an ETL pipeline, stores the processed data in a PostgreSQL data warehouse using a **star schema**, and exposes the data through a Flask application for analysis and visualisation.

The project is designed to answer questions such as:

* Which programming languages are growing the fastest?
* Which technologies are most popular?
* How do repository stars and contributors change over time?
* Which repositories and technology areas are attracting the most attention?

## Architecture

The platform follows a **Bronze → Silver → Gold** data architecture.

## Features

* Extracts GitHub repository data using the GitHub API
* Stores raw API responses in the Bronze layer
* Cleans and transforms repository data
* Stores processed data as CSV files in the Silver layer
* Loads processed data into a PostgreSQL data warehouse
* Uses a star-schema design for analytical queries
* Provides a Flask web application
* Exposes processed data through API endpoints
* Displays repository and technology trends through a JavaScript dashboard
* Supports scheduled pipeline execution
* Uses environment variables for API credentials and configuration

## Data Architecture

### Bronze Layer

The Bronze layer contains the raw responses received from the GitHub API.

```text
data/bronze/
├── raw_repo_2026-06-21.json
├── raw_repo_2026-06-22.json
├── raw_repo_2026-07-11.json
├── raw_repo_2026-07-13.json
└── ...
```

Raw data is preserved before any transformation takes place.

Keeping the original data makes it possible to:

* Reprocess data
* Debug transformation issues
* Audit the original API responses
* Compare changes in the transformation process

### Silver Layer

The Silver layer contains cleaned and transformed repository data.

```text
data/silver/
├── cleaned_repo_2026-06-22.csv
├── cleaned_repo_2026-07-11.csv
├── cleaned_repo_2026-07-13.csv
├── cleaned_repo_2026-07-14.csv
└── ...
```

The transformation process converts the raw API responses into structured CSV data suitable for loading into the PostgreSQL data warehouse.

### Gold Layer

The Gold layer contains the processed data in PostgreSQL.

The data warehouse uses a **star schema** to separate measurable repository metrics from descriptive information.

```text
                         ┌───────────────┐
                         │   dim_date    │
                         └───────┬───────┘
                                 │
                                 │
┌──────────────┐                 ▼                 ┌─────────────────┐
│ dim_language │──────────► fact_repo_snapshot ◄──│ dim_repository  │
└──────────────┘                 ▲                 └─────────────────┘
                                 │
                                 │
                         ┌───────┴───────┐
                         │   dim_owner   │
                         └───────────────┘
```

The fact table stores measurable repository metrics while the dimension tables provide descriptive context for analysis.

### Fact Table

The repository snapshot fact table stores measurable repository metrics such as:

* Stars
* Forks
* Watchers
* Contributors
* Snapshot date
* Repository
* Language
* Owner

Taking repository snapshots over time makes it possible to analyse **growth and trends**, rather than only looking at the current state of a repository.

### Dimension Tables

The warehouse uses dimension tables to provide descriptive information about repository data.

The dimensions include:

* `dim_date`
* `dim_language`
* `dim_owner`
* `dim_repository`

This structure allows analytical queries to join repository metrics with information about the repository, owner, programming language, and date.

## ETL Pipeline

The pipeline follows the traditional **Extract → Transform → Load (ETL)** process.

### 1. Extract

`extraction.py` retrieves repository data from the GitHub API.

```text
GitHub API
    ↓
Raw JSON
    ↓
data/bronze/
```

The raw API response is stored before transformation so that the original data is preserved.

### 2. Transform

`transformation.py` processes the extracted repository data.

```text
Raw JSON
    ↓
Parse / Flatten
    ↓
Clean
    ↓
Validate
    ↓
Transform
    ↓
Silver CSV
```

The transformation stage converts raw API data into a consistent structure suitable for database loading.

The transformed data is stored in the Silver layer.

### 3. Load

`load.py` loads the transformed data into PostgreSQL.

```text
Silver Data
    ↓
PostgreSQL
    ↓
Fact + Dimension Tables
```

The PostgreSQL database represents the Gold layer of the pipeline and provides structured data for analytical queries and the application.

### 4. Pipeline Orchestration

`pipeline.py` coordinates the different stages of the ETL process.

```text
Extraction
     ↓
Transformation
     ↓
Loading
```

This provides a single entry point for running the complete pipeline.

## Scheduling

`scheduler.py` is responsible for scheduling pipeline executions.

This allows repository data to be collected periodically rather than requiring manual triggers.

Scheduled execution allows the dataset to grow over time, making it possible to analyse changes in repository activity and technology trends.

## Web Application

The project includes a Flask application that provides access to the processed data.

```text
app.py
  ├── Flask
  ├── PostgreSQL
  └── Dashboard
```

### Frontend Stack

* HTML
* CSS
* JavaScript
* Chart.js

The dashboard provides an interactive visual interface for exploring collected GitHub technology trends.

## API

The Flask application provides endpoints for accessing processed repository data.

Example endpoints include:

```text
GET /repos
GET /languages
GET /load_data
```

The API returns structured data that can be consumed by the frontend dashboard or other applications.

> **Note:** The production Gold layer is PostgreSQL.`data/gold/github-trends.db` represents an earlier SQLite development/prototype artefact and is not the PostgreSQL warehouse used by the current application.

## Technology Stack

| Technology    | Purpose                               |
| ------------- | ------------------------------------- |
| Python        | ETL pipeline and application logic    |
| Pandas        | Data processing and transformation    |
| JSON          | Raw API data format                   |
| CSV           | Intermediate/Silver data format       |
| PostgreSQL    | Data warehouse                        |
| SQL           | Data modelling and analytical queries |
| Flask         | Web application and REST API          |
| JavaScript    | Dashboard functionality               |
| HTML / CSS    | Frontend styling and layout           |
| Chart.js      | Data visualisation                    |
| python-dotenv | Environment variable management       |
| Git           | Version control                       |

## Data Pipeline Flow

The complete flow of the application:

```text
GitHub API
    │
    ▼
┌───────────────┐
│  Extraction   │
└───────┬───────┘
        │
        ▼
  Bronze Layer
   (Raw JSON)
        │
        ▼
┌───────────────┐
│ Transformation│
└───────┬───────┘
        │
        ▼
  Silver Layer
  (Clean CSV)
        │
        ▼
┌───────────────┐
│     Load      │
└───────┬───────┘
        │
        ▼
   Gold Layer
  (PostgreSQL)
        │
        ▼
   Flask App
        │
        ▼
    Dashboard
```

## Example Analytical Questions

Once the data has been loaded into the warehouse, SQL can be used to investigate questions such as:

* Which programming languages have the most repositories?
* Which repositories have the most stars?
* Which languages are growing the fastest?
* How does repository activity change over time?
* What are the average stars for repositories using a particular language?
* Which repositories have the most contributors?
* How does technology popularity change over time?

Example analytical query:

```sql
-- Which languages have the most repository snapshots?

SELECT
    l.language_name,
    COUNT(*) AS repository_count
FROM fact_repo_snapshot f
JOIN dim_language l
    ON f.language_id = l.language_id
GROUP BY l.language_name
ORDER BY repository_count DESC;
```

## Data Quality

The pipeline accounts for common problems encountered when working with real-world API data, including:

* Missing fields
* Null values
* Inconsistent data types
* Nested JSON responses
* Duplicate records
* API response variations

Rather than assuming that incoming data is always clean, the pipeline validates and transforms the data before loading it into the warehouse.

## Getting Started

### Prerequisites

Make sure you have the following installed:

* Python 3.x
* Git
* PostgreSQL
* A GitHub account
* A GitHub personal access token

### 1. Clone the Repository

Clone the repository using SSH:

```bash
git clone git@github.com:MamelloMolokwane/Github-trends.git
cd Github-trends
```

### 2. Create a Virtual Environment

#### Windows

```powershell
python -m venv .venv
.venv\Scripts\activate
```

#### Linux / macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Create a `.env` file in the project root.

```env
GITHUB_TOKEN=your_github_token
```

Add the PostgreSQL connection settings required by the application.

For example:

```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=github_trends
DB_USER=your_username
DB_PASSWORD=your_password
```

### 5. Configure PostgreSQL

Create the PostgreSQL database used by the application.

For example:

```sql
CREATE DATABASE github_trends;
```

Configure the connection details in your `.env` file according to the variables expected by the application.

### 6. Run the ETL Pipeline

Run the complete extraction, transformation, and loading pipeline:

```bash
python scripts/pipeline.py
```

The pipeline:

1. Extracts repository data from GitHub
2. Stores raw responses in the Bronze layer
3. Cleans and transforms the data
4. Stores cleaned data in the Silver layer
5. Loads the data into the PostgreSQL Gold layer

### 7. Run the Flask Application

Start the local development server:

```bash
python app.py
```

Access the dashboard through the local URL displayed in your terminal.

Typically:

```text
http://127.0.0.1:5000
```

## Testing

Automated tests are located in:

```text
tests/
```

The tests cover the ETL pipeline components, including:

* Data extraction
* Data transformation
* Data loading
* Data validation
* Common data-quality edge cases

## Data Engineering Concepts Demonstrated

This project demonstrates practical experience with:

* ETL pipeline development
* Data ingestion
* REST API consumption
* JSON processing
* Data cleaning
* Data transformation
* Data validation
* Medallion architecture
* Bronze/Silver/Gold data layers
* Relational database design
* Star-schema modelling
* Fact and dimension tables
* Data warehousing
* Analytical SQL
* Pipeline orchestration
* Scheduled data collection
* REST API development
* Web application development
* Data visualisation
* Environment configuration
* Version control
* Handling real-world data-quality issues

## Future Improvements

* [ ] Implement end-to-end automated integration testing
* [ ] Add automated data-quality validation rules
* [ ] Implement incremental data loading
* [ ] Expand metrics collection, such as issue counts and commit frequency
* [ ] Add advanced analytical dashboard views
* [ ] Containerise the application using Docker
* [ ] Build CI/CD pipelines using GitHub Actions
* [ ] Add robust exception handling and logging
* [ ] Implement automated retry and backoff logic for API failures
* [ ] Deploy the application and dashboard
* [ ] Expand historical trend analysis

## What This Project Demonstrates

The core goal of this project is to illustrate how raw external data can be transformed into meaningful metrics that can be consumed by an application.

Rather than working with a static dataset, the project retrieves data from an external API and processes it through multiple stages:

```text
External Data Source
        │
        ▼
    Ingestion
        │
        ▼
   Raw Storage
        │
        ▼
 Transformation
        │
        ▼
  Cleaned Data
        │
        ▼
 Data Warehouse
        │
        ▼
  Analytical SQL
        │
        ▼
   Flask API
        │
        ▼
  Visualisation
```

It showcases the fundamentals of building a modular, end-to-end data engineering platform from **raw API ingestion to end-user visualisation**.


WTC-CJ8UDD7D