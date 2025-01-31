from groq import Groq
import streamlit as st
import re
from typing import Dict, List, Tuple
from .database import get_all_tables, get_table_schema, get_table_relationships, get_database_connection, execute_sql_query

def get_schema_metadata() -> Dict:
    """Get complete schema metadata for validation"""
    tables = get_all_tables()
    schema_metadata = {}
    
    for table in tables:
        columns = get_table_schema(table)
        schema_metadata[table] = {
            'columns': [col[0] for col in columns],
            'column_types': {col[0]: col[1] for col in columns}
        }
        
    relationships = get_table_relationships()
    if relationships:
        schema_metadata['relationships'] = relationships
        
    return schema_metadata

def generate_table_aliases(tables: List[str]) -> Dict[str, str]:
    """Generate consistent table aliases based on table names"""
    aliases = {}
    used_abbreviations = set()
    
    for table in tables:
        words = table.split('_')
        if len(words) > 1:
            # Use first letter of each word
            abbrev = ''.join(word[0] for word in words)
        else:
            # Use first two letters for single word
            abbrev = table[:2]
        
        # Handle duplicates
        base_abbrev = abbrev
        counter = 1
        while abbrev in used_abbreviations:
            abbrev = f"{base_abbrev}{counter}"
            counter += 1
            
        aliases[table] = abbrev.lower()
        used_abbreviations.add(abbrev)
    
    return aliases

def prepare_schema_prompt(schema_metadata: Dict) -> str:
    """Prepare the database schema information with dynamic relationships"""
    schema_info = []
    tables = [t for t in schema_metadata.keys() if t != 'relationships']
    aliases = generate_table_aliases(tables)
    
    # Table structure
    for table in tables:
        cols = schema_metadata[table]['columns']
        cols_info = [f"    - {col}" for col in cols]
        table_info = f"\n{table} (alias: {aliases[table]}):\n" + "\n".join(cols_info)
        schema_info.append(table_info)
    
    # Relationships
    relationships = schema_metadata.get('relationships', [])
    rel_info = []
    for rel in relationships:
        from_table, to_table = rel[1], rel[4]
        rel_info.append(
            f"{aliases[from_table]}.{rel[2]} -> {aliases[to_table]}.{rel[5]}"
        )
    
    schema_prompt = "## Tables and Columns\n" + "\n".join(schema_info)
    if rel_info:
        schema_prompt += "\n\n## Relationships\n" + "\n".join(rel_info)
    
    return schema_prompt, aliases

def get_sql_prompt(user_question: str, schema_metadata: Dict) -> str:
    """Create the full prompt for SQL generation"""
    schema_prompt, aliases = prepare_schema_prompt(schema_metadata)
    
    prompt = (
        f"Generate a PostgreSQL query to answer: {user_question}\n\n"
        f"Use these requirements:\n"
        f"1. Use EXACT table and column names from below\n"
        f"2. Use the given table aliases\n"
        f"3. Put double quotes around ALL identifiers\n"
        f"4. If data isn't available, respond with 'SCHEMA_ERROR: Required data not available'\n\n"
        f"{schema_prompt}\n\n"
        f"SQL Query:"
    )
    
    return prompt

# def get_sql_prompt(user_question: str) -> str:
#     """Create the full prompt for SQL generation"""
#     schema = prepare_schema_prompt()
#     tables = get_all_tables()
#     aliases = generate_table_aliases(tables)
#     schema_metadata = get_schema_metadata()

#     # Create the aliases string
#     alias_str = '\n'.join([f'   - "{table}" => {alias}' for table, alias in aliases.items()])
    
#     # Get the first relationship to create a dynamic example
#     relationships = get_table_relationships()
#     example_query = ""
#     if relationships and len(relationships) > 0:
#         # Get first relationship for example
#         rel = relationships[0]
#         from_table, from_col = rel[1], rel[2]
#         to_table, to_col = rel[4], rel[5]
#         from_alias = aliases[from_table]
#         to_alias = aliases[to_table]
        
#         # Get a sample column from each table
#         from_cols = schema_metadata.get(from_table, {}).get('columns', [])
#         to_cols = schema_metadata.get(to_table, {}).get('columns', [])
        
#         sample_from_col = next((col for col in from_cols if col != from_col), from_col)
#         sample_to_col = next((col for col in to_cols if col != to_col), to_col)
        
#         example_query = (
#             f"\nExample of correct query format:\n"
#             f'SELECT {from_alias}."{sample_from_col}", {to_alias}."{sample_to_col}"\n'
#             f'FROM "{from_table}" {from_alias}\n'
#             f'JOIN "{to_table}" {to_alias} ON {from_alias}."{from_col}" = {to_alias}."{to_col}";\n'
#         )
    
#     # Create list of all available tables and columns for validation
#     available_tables = "\n".join(f"- {table}" for table in tables)
#     table_columns = "\n".join(
#         f"- {table}: " + ", ".join(f'"{col[0]}"' for col in get_table_schema(table))
#         for table in tables
#     )
    
#     prompt = (
#         f"You are a PostgreSQL expert. Generate a SQL query using ONLY the available tables and columns listed below.\n\n"
#         f"Available Tables:\n{available_tables}\n\n"
#         f"Available Columns per Table:\n{table_columns}\n\n"
#         f"Table Aliases to Use:\n{alias_str}\n\n"
#         f"Schema Details:\n{schema}\n"
#         f"{example_query}\n"
#         f"User Question: {user_question}\n\n"
#         f"Critical Requirements:\n"
#         f"1. ONLY use tables and columns from the lists above\n"
#         f"2. Use DOUBLE QUOTES around ALL table and column names\n"
#         f"3. Use the EXACT table aliases provided\n"
#         f"4. Do not make up or infer any tables or columns\n"
#         f"5. If you cannot answer with the available tables/columns, say 'Cannot answer - required data not in schema'\n\n"
#         f"SQL Query:")
    
#     return prompt

def clean_sql_query(sql: str, schema_metadata: Dict) -> str:
    """Clean and validate SQL query"""
    if "SCHEMA_ERROR" in sql:
        raise ValueError("The required data is not available in the schema")
        
    # Remove markup and clean whitespace
    sql = re.sub(r'```sql\s*|\s*```', '', sql, flags=re.IGNORECASE).strip()
    if not sql:
        raise ValueError("Generated SQL query is empty")
        
    # Basic validation
    tables = [t for t in schema_metadata.keys() if t != 'relationships']
    for table in tables:
        if table not in sql and f'"{table}"' not in sql:
            continue
        cols = schema_metadata[table]['columns']
        for col in cols:
            if col in sql and f'"{col}"' not in sql:
                sql = sql.replace(col, f'"{col}"')
    
    return sql

def validate_query(sql: str, schema_metadata: Dict) -> bool:
    """Full query validation against schema"""
    tables = [t for t in schema_metadata.keys() if t != 'relationships']
    relationships = schema_metadata.get('relationships', [])
    
    # Check all referenced tables exist
    used_tables = re.findall(r'"(\w+)"', sql)
    for table in set(used_tables):
        if table not in tables:
            raise ValueError(f"Table {table} does not exist")
    
    # Check columns
    column_matches = re.findall(r'"(\w+)"."(\w+)"', sql)
    for table, column in column_matches:
        if table not in schema_metadata:
            raise ValueError(f"Table {table} not in schema")
        if column not in schema_metadata[table]['columns']:
            raise ValueError(f"Column {table}.{column} does not exist")
    
    # Check joins against known relationships
    joins = re.findall(r'JOIN\s+"(\w+)"\s+ON\s+"(\w+)"."(\w+)"\s*=\s*"(\w+)"."(\w+)"', sql, re.IGNORECASE)
    for join in joins:
        found = any(
            rel[1] == join[0] and rel[2] == join[2] and rel[4] == join[3] and rel[5] == join[4]
            for rel in relationships
        )
        if not found:
            st.warning(f"Unrecognized join: {join[0]}.{join[2]} = {join[3]}.{join[4]}")
    
    return True

def process_question(user_question: str) -> Tuple[str, List[Dict], str]:
    """Process user question and return query results"""
    try:
        # Initialize Groq client
        client = Groq(api_key=st.secrets["GROQ_API_KEY"])
        
        # Get schema metadata
        schema_metadata = get_schema_metadata()
        
        # Generate SQL
        sql_prompt = get_sql_prompt(user_question, schema_metadata)
        completion = client.chat.completions.create(
            messages=[{"role": "user", "content": sql_prompt}],
            model="llama-3.3-70b-versatile"
        )
        raw_sql = completion.choices[0].message.content
        
        # Clean and validate SQL
        try:
            cleaned_sql = clean_sql_query(raw_sql, schema_metadata)
        except ValueError as e:
            return "", [], str(e)
            
        # Execute query
        results, columns = execute_sql_query(cleaned_sql)
        if not results:
            return cleaned_sql, [], "No results found for your query"
            
        # Generate natural language response
        nl_prompt = f"Question: {user_question}\nResults: {results}\nProvide a natural response:"
        response = client.chat.completions.create(
            messages=[{"role": "user", "content": nl_prompt}],
            model="llama-3.3-70b-versatile"
        )
        
        return cleaned_sql, results, response.choices[0].message.content
        
    except Exception as e:
        error_msg = str(e)
        if "table" in error_msg.lower() and "does not exist" in error_msg.lower():
            return "", [], "I cannot answer this question with the available data. Please try a different question."
        return "", [], f"Error: {error_msg}"