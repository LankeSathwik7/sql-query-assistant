# 🤖 SQL Query Assistant

A Streamlit-based application that allows users to query their PostgreSQL database using natural language questions. The app leverages the Groq LLM API to convert natural language queries into SQL and provide human-readable answers.

## ✨ Features

- 🤖 Natural language to SQL conversion
- 📊 Interactive database schema visualization
- 📈 Real-time query results with data visualization
- 💾 CSV export functionality
- 🔍 Sample data preview for all tables
- 📝 Detailed database statistics
- 🔗 Table relationship visualization

## 📋 Prerequisites

- Python 3.8+
- PostgreSQL database
- Groq API key
- Streamlit account (for secrets management)

## 🚀 Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd sql-query-assistant
```

2. Install required packages:
```bash
pip install -r requirements.txt
```

3. Set up your environment variables in `.streamlit/secrets.toml`:
```toml
DATABASE_URL = "your-postgresql-connection-string"
DATABASE_NAME = "your-database-name"
GROQ_API_KEY = "your-groq-api-key"
```

## 📂 Project Structure

```
.
├── LICENSE                 # Apache License 2.0
├── README.md              # Project documentation
├── requirements.txt       # Project dependencies
├── src/
│   ├── __init__.py
│   ├── database.py       # Database connection and operations
│   └── llm_chain.py      # LLM integration and query processing
└── streamlit_app.py      # Main Streamlit application
```

## ⚙️ Configuration

### 🗄️ Database Connection

The application uses PostgreSQL as its database. Configure your database connection in `.streamlit/secrets.toml`:

```toml
DATABASE_URL = "postgresql://username:password@host:port/database?sslmode=require"
DATABASE_NAME = "Your Database Name"
```

### 🧠 LLM Integration

The application uses Groq's LLM API for natural language processing. Add your API key to `.streamlit/secrets.toml`:

```toml
GROQ_API_KEY = "your-groq-api-key"
```

## 📦 Required Dependencies

The following packages are required and can be installed via requirements.txt:
- streamlit
- psycopg2-binary
- google-generativeai
- pandas
- groq

## 🏃‍♂️ Running the Application

1. Start the Streamlit application:
```bash
streamlit run streamlit_app.py
```

2. Open your browser and navigate to the provided URL (typically http://localhost:8501)

## 📱 Usage

1. **View Database Schema**: 
   - The sidebar displays all tables, their columns, and relationships
   - Sample data is available for each table
   - Database statistics show total tables, rows, and database size

2. **Query Your Data**:
   - Enter your question in natural language
   - Click "Get Answer" to process your query
   - View the generated SQL, results table, and natural language explanation
   - Download results as CSV if needed

3. **Example Questions**:
   - "Show total revenue by category"
   - "Which products have the highest sales quantity?"
   - "List top 5 customers by order value"

## 🔒 Security Features

- SQL injection prevention through proper query sanitization
- Secure credential management using Streamlit secrets
- Parameterized queries for safe database operations

## 🔧 Technical Details

### 🧩 Components

1. **database.py**:
   - Handles all database operations
   - Manages connections and queries
   - Provides schema information

2. **llm_chain.py**:
   - Processes natural language questions
   - Generates SQL queries using Groq LLM
   - Creates natural language responses

3. **streamlit_app.py**:
   - Main application interface
   - Handles user interaction
   - Displays results and visualizations

### ⚡ Query Processing Flow

1. User inputs a natural language question
2. System generates database schema context
3. Groq LLM converts question to SQL
4. Query is validated and executed
5. Results are formatted and displayed
6. Natural language explanation is generated

## ⚠️ Error Handling

- Database connection errors are gracefully handled
- Invalid queries are caught and reported
- LLM API errors are managed with appropriate user feedback

## 🤝 Contributing

Please feel free to submit issues and pull requests for any improvements.

## 📄 License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with [Streamlit](https://streamlit.io/)
- Powered by [Groq](https://groq.com/) LLM API
- Uses [PostgreSQL](https://www.postgresql.org/) for database management