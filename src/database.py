import psycopg2
from psycopg2.extras import RealDictCursor
import streamlit as st
from typing import List, Tuple, Dict, Optional

def get_database_connection():
    """Create database connection using Streamlit secrets"""
    try:
        conn = psycopg2.connect(st.secrets["DATABASE_URL"])
        return conn
    except Exception as e:
        st.error(f"Error connecting to database: {e}")
        return None

def get_database_name() -> str:
    """Get the display name for the database"""
    try:
        return st.secrets["DATABASE_NAME"]
    except:
        return "Database"  # fallback name
    
def get_all_tables() -> List[str]:
    """Get list of all tables in the database"""
    conn = get_database_connection()
    if not conn:
        return []
    
    try:
        with conn.cursor() as cur:
            # Query to get all tables
            cur.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                AND table_type = 'BASE TABLE'
                ORDER BY table_name;
            """)
            tables = [row[0] for row in cur.fetchall()]
        return tables
    except Exception as e:
        st.error(f"Error fetching tables: {e}")
        return []
    finally:
        conn.close()

def get_table_schema(table_name: str) -> List[Tuple]:
    """Get schema information for a specific table"""
    conn = get_database_connection()
    if not conn:
        return []
    
    try:
        with conn.cursor() as cur:
            # Query to get column information
            cur.execute("""
                SELECT 
                    column_name,
                    data_type,
                    is_nullable,
                    column_default
                FROM information_schema.columns
                WHERE table_name = %s
                AND table_schema = 'public'
                ORDER BY ordinal_position;
            """, (table_name,))
            columns = cur.fetchall()
        return columns
    except Exception as e:
        st.error(f"Error fetching schema for {table_name}: {e}")
        return []
    finally:
        conn.close()

def get_table_relationships() -> List[Tuple]:
    """Get foreign key relationships between tables"""
    conn = get_database_connection()
    if not conn:
        return []
    
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT
                    tc.table_schema, 
                    tc.table_name, 
                    kcu.column_name,
                    ccu.table_schema AS foreign_table_schema,
                    ccu.table_name AS foreign_table_name,
                    ccu.column_name AS foreign_column_name
                FROM 
                    information_schema.table_constraints AS tc 
                    JOIN information_schema.key_column_usage AS kcu
                      ON tc.constraint_name = kcu.constraint_name
                      AND tc.table_schema = kcu.table_schema
                    JOIN information_schema.constraint_column_usage AS ccu
                      ON ccu.constraint_name = tc.constraint_name
                      AND ccu.table_schema = tc.table_schema
                WHERE tc.constraint_type = 'FOREIGN KEY'
                ORDER BY tc.table_name;
            """)
            relationships = cur.fetchall()
        return relationships
    except Exception as e:
        st.error(f"Error fetching relationships: {e}")
        return []
    finally:
        conn.close()

def get_database_stats() -> Optional[Dict]:
    """Get database statistics"""
    conn = get_database_connection()
    if not conn:
        return None
    
    try:
        with conn.cursor() as cur:
            # Get database size
            cur.execute("""
                SELECT pg_size_pretty(pg_database_size(current_database())) as db_size;
            """)
            db_size = cur.fetchone()[0]
            
            # Get number of tables
            cur.execute("""
                SELECT COUNT(*) 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                AND table_type = 'BASE TABLE';
            """)
            table_count = cur.fetchone()[0]
            
            # Get row counts for each table
            total_rows = 0
            tables = get_all_tables()
            for table in tables:
                try:
                    cur.execute(f'SELECT COUNT(*) FROM "{table}";')
                    count = cur.fetchone()[0]
                    total_rows += count if count else 0
                except Exception as e:
                    st.warning(f"Couldn't count rows in {table}: {e}")
            
            return {
                "size": db_size,
                "tables": table_count,
                "total_rows": total_rows
            }
    except Exception as e:
        st.error(f"Error fetching database stats: {e}")
        return None
    finally:
        conn.close()

def execute_sql_query(query: str) -> Tuple[List[Dict], List[str]]:
    """Execute a SQL query and return results with column names
    
    Args:
        query (str): SQL query to execute
        
    Returns:
        Tuple[List[Dict], List[str]]: Tuple containing:
            - List of result rows as dictionaries
            - List of column names
    """
    conn = get_database_connection()
    if not conn:
        return [], []
    
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query)
            results = cur.fetchall()
            
            # Get column names from cursor description
            columns = [desc[0] for desc in cur.description] if cur.description else []
            
            return list(results), columns
            
    except Exception as e:
        st.error(f"Error executing query: {e}")
        return [], []
    finally:
        conn.close()

def get_table_preview(table_name: str, limit: int = 5) -> List[Dict]:
    """Get preview rows from a table"""
    conn = get_database_connection()
    if not conn:
        return []
    
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(f'SELECT * FROM "{table_name}" LIMIT %s;', (limit,))
            preview = cur.fetchall()
        return preview
    except Exception as e:
        st.error(f"Error fetching preview for {table_name}: {e}")
        return []
    finally:
        conn.close()

def test_database_connection() -> bool:
    """Test database connection and print schema information"""
    try:
        tables = get_all_tables()
        if not tables:
            return False
        
        print("Connected successfully!")
        print("\nAvailable tables:")
        
        for table in tables:
            print(f"\n{table}:")
            columns = get_table_schema(table)
            for col in columns:
                print(f"  - {col[0]} ({col[1]})")
        
        relationships = get_table_relationships()
        if relationships:
            print("\nTable relationships:")
            for rel in relationships:
                print(f"{rel[1]}.{rel[2]} -> {rel[4]}.{rel[5]}")
        
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    # Test the database connection when run directly
    test_database_connection()