import re
from typing import Tuple, List, Dict, Optional
from groq import Groq
import streamlit as st
from .database import get_all_tables, get_table_schema, get_database_connection

def get_db_schema_context() -> str:
    """Generate database schema context for the LLM"""
    context = ["Database Schema:"]
    
    tables = get_all_tables()
    for table in tables:
        context.append(f"\nTable: {table}")
        columns = get_table_schema(table)
        for col in columns:
            col_name, col_type, is_nullable, default = col
            nullable_text = "NULL" if is_nullable == "YES" else "NOT NULL"
            context.append(f"  - {col_name} ({col_type}) {nullable_text}")
    
    return "\n".join(context)

def sanitize_sql(query: str) -> str:
    """Remove Markdown formatting and backticks from SQL query"""
    # Remove code block markers
    query = re.sub(r'```sql', '', query, flags=re.IGNORECASE)
    query = re.sub(r'```', '', query)
    
    # Remove leading/trailing whitespace and quotes
    query = query.strip().strip('"').strip("'")
    
    # Ensure semicolon at end
    if not query.endswith(';'):
        query += ';'
        
    return query

def generate_sql_query(question: str, schema_context: str) -> str:
    """Generate SQL query using Groq"""
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
    
    prompt = f"""Given this database schema:
{schema_context}

Generate a SQL query for: {question}

Follow these strict rules:
1. Identifier Handling:
   - Only quote identifiers with spaces/special characters using standard double quotes
   - Never nest quotes or use backslash escaping
   - Use snake_case names without quotes when possible
   - Treat all identifiers as case-insensitive unless explicitly quoted

2. Syntax Requirements:
   - Use explicit JOIN syntax (INNER/LEFT/RIGHT/OUTER JOIN) never comma-separated FROMs
   - Always qualify columns with table aliases
   - Use CAST() for type conversions instead of :: operator
   - Handle NULLs with IS NULL/IS NOT NULL never '= NULL'
   - Use COALESCE() for default values
   - Always include ORDER BY with LIMIT

3. Security & Safety:
   - Use parameterization ($1, $2) for values
   - Prevent SQL injection through proper quoting
   - Avoid deprecated constructs like *= joins

4. Compatibility:
   - Use standard SQL functions (EXTRACT() not DATEPART())
   - ANSI-compatible string literals (single quotes only)
   - ISO-8601 date formats (YYYY-MM-DD)
   - Use LIMIT instead of TOP/FETCH FIRST

5. Error Prevention:
   - Validate table/column names against schema
   - Ensure JOIN conditions match indexed columns
   - Handle potential division by zero
   - Consider NULLs in WHERE conditions
   - Avoid SELECT * (list explicit columns)

6. Formatting:
   - Use table aliases (FROM table AS t)
   - Standard capitalization (SELECT/FROM in uppercase)
   - Indentation for readability
   - Semicolon terminator

Return ONLY the SQL query with these characteristics, no explanations. Verify against this example structure:

SELECT o.order_id, c."customer name" 
FROM orders AS o
JOIN customers AS c ON o.cust_id = c.id
WHERE c.region = 'West'
  AND o.order_date > CAST('2023-01-01' AS DATE)
ORDER BY o.order_date DESC
LIMIT 10;"""

    response = client.chat.completions.create(
        messages=[{
            "role": "user",
            "content": prompt
        }],
        model="llama-3.3-70b-versatile",
        temperature=0.1,
        max_tokens=500
    )
    raw_sql = response.choices[0].message.content.strip()
    return sanitize_sql(raw_sql)

# def generate_sql_query(question: str, schema_context: str) -> str:
#     """Generate SQL query using Groq"""
#     client = Groq(api_key=st.secrets["GROQ_API_KEY"])
    
#     prompt = f"""Given the following database schema:

# {schema_context}

# Generate a SQL query to answer this question: {question}

# Important rules for the SQL query:
# 1. Use double quotes for table aliases and column names
# 2. For column names containing spaces, just use double quotes, no special escaping needed
# 3. The query must be compatible with PostgreSQL
# 4. Don't use quotes within quotes for column names

# Return ONLY the SQL query, nothing else."""

#     response = client.chat.completions.create(
#         messages=[{
#             "role": "user",
#             "content": prompt
#         }],
#         model="llama-3.3-70b-versatile",  # or your preferred Groq model
#         temperature=0.1,
#         max_tokens=500
#     )
    
#     return response.choices[0].message.content.strip()

def execute_query(query: str) -> List[Dict]:
    """Execute SQL query and return results"""
    conn = get_database_connection()
    if not conn:
        return []
    
    try:
        with conn.cursor() as cur:
            cur.execute(query)
            columns = [desc[0] for desc in cur.description]
            results = []
            for row in cur.fetchall():
                results.append(dict(zip(columns, row)))
            return results
    except Exception as e:
        st.error(f"Error executing query: {e}")
        return []
    finally:
        conn.close()

def generate_nl_response(question: str, query: str, results: List[Dict]) -> str:
    """Generate natural language response using Groq"""
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
    
    # Convert results to string representation
    results_str = "\n".join([str(row) for row in results[:5]])
    if len(results) > 5:
        results_str += "\n..."

    prompt = f"""Question: {question}

SQL Query Used:
{query}

Query Results:
{results_str}

Please provide a clear, natural language response that answers the original question based on these results. Keep it concise but informative."""

    response = client.chat.completions.create(
        messages=[{
            "role": "user",
            "content": prompt
        }],
        model="llama-3.3-70b-versatile",  # or your preferred Groq model
        temperature=0.7,
        max_tokens=200
    )
    
    return response.choices[0].message.content.strip()

def process_question(question: str) -> Tuple[str, List[Dict], str]:
    """Process user question and return SQL query, results, and natural language response"""
    # Get database schema context
    schema_context = get_db_schema_context()
    
    # Generate SQL query
    sql_query = generate_sql_query(question, schema_context)

    # Add validation
    if not sql_query.lower().startswith(('select', 'insert', 'update', 'delete')):
        st.error("Generated query appears invalid. Please check your question.")
        return "", [], ""
    
    # Execute query
    results = execute_query(sql_query)
    
    # Generate natural language response
    nl_response = generate_nl_response(question, sql_query, results)
    
    return sql_query, results, nl_response