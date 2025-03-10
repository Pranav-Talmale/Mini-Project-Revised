# DocGene

DocGene is an educational data management system with natural language query capabilities, batch formation for student groups, and RESTful API support for mobile applications.

## Features

- **Natural Language Database Queries**: Talk to your database in plain English
- **Student Batch Formation**: Group students based on their subject combinations
- **Interactive Analytics**: Visualize student and subject data
- **Mobile API**: Comprehensive REST API for mobile integration
- **Excel/CSV Import**: Import data directly from spreadsheets
- **Multi-Database Support**: Works with SQLite, PostgreSQL, MySQL, and more

## Getting Started

### Prerequisites

- Python 3.8+
- pip package manager
- PostgreSQL (optional, SQLite works out of the box)

### Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/docgene.git
cd docgene
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up your environment variables by creating a `.env` file:
```
# Database Configuration
SQLITE_DB_DRIVER=sqlite
SQLITE_DB_PATH=.
SQLITE_DB_NAME=students

# LLM Configuration (if using)
LLM_BACKEND=gemini
LLM_API_KEY=your_api_key_here
LLM_ENDPOINT=https://generativelanguage.googleapis.com
```

### Running the Application

Start the Streamlit web interface:

```bash
streamlit run db-agent.py
```

The application will be available at `http://localhost:8501`

## Usage Guide

### Database Setup

1. Navigate to the "Database Configuration" section in the sidebar
2. Select your database driver (SQLite, PostgreSQL, MySQL, etc.)
3. Enter your connection details
4. Click "Save DB Config"

### Importing Data

1. Go to the "Import Data From Excel or CSV" section
2. Upload your Excel or CSV file
3. Configure the database name and path
4. Click "Save Config"

### Querying Your Data

1. Type your natural language query in the text area
2. Click "Execute" to run the query
3. View the generated SQL and results

### Batch Formation

1. Navigate to the "Batch Formation" page
2. Select a division
3. Set the number of batches
4. Click "Generate Batches"
5. Review and save the batch assignments

## API Server

DocGene includes a REST API for mobile application integration.

### Starting the API Server

```bash
python -m api.main
```

The API will be available at `http://localhost:8000`. Interactive documentation can be accessed at `http://localhost:8000/docs`.

### API Endpoints

- `/api/students` - Student management
- `/api/subjects` - Subject management
- `/api/enrollments` - Enrollment tracking
- `/api/batches` - Batch formation
- `/api/analytics` - Data analytics

## Docker Support

You can also run DocGene using Docker:

```bash
# Build the Docker image
docker build -t docgene .

# Run the container
docker run -p 8501:8501 -p 8000:8000 docgene
```

## Project Structure

```
docgene/
├── api/                 # API implementation
│   ├── middleware/      # Database middleware
│   └── routes/          # API endpoints
├── connectors/          # Database connectors
├── helpers/             # Utility functions
├── pages/               # Streamlit pages
├── scripts/             # Database scripts
├── db-agent.py          # Main application entry point
├── batch_utils.py       # Batch formation utilities
├── dashboard_integration.py  # Analytics dashboard
└── setup_batch_database.py   # Database setup script
```

## Development

### Adding New Features

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Running Tests

```bash
# Run API tests
pytest api/tests/

# Run web interface tests
pytest tests/
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- SQLAlchemy for database ORM
- Streamlit for the web interface
- FastAPI for the REST API
- Plotly for data visualization