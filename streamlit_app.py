# import streamlit as st

# st.title("🎈 My new app")
# st.write(
#     "Let's start building! For help and inspiration, head over to [docs.streamlit.io](https://docs.streamlit.io/)."
# )

import streamlit as st
import pandas as pd
from src.database import (
    get_all_tables, 
    get_table_schema, 
    get_table_relationships,
    get_database_stats,
    get_table_preview,
    get_database_name
)
from src.llm_chain import process_question

# Page configuration
st.set_page_config(
    page_title="SQL Query Assistant",
    page_icon="🤖",
    layout="wide"
)

def format_currency(value):
    """Format number as currency"""
    try:
        if isinstance(value, (int, float)):
            return f"${value:,.2f}"
        return value
    except:
        return value

def main():
    # Get database name
    db_name = get_database_name()

    st.title("SQL Query Assistant 🤖")
    
    # Sidebar - Database Schema Information
    with st.sidebar:
        st.header(f"{db_name} Schema")
        #st.header("Database Schema")
        
        # Add database statistics
        stats = get_database_stats()
        if stats:
            st.write("📊 **Database Statistics**")
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Tables", stats["tables"])
                st.metric("Total Rows", f"{stats['total_rows']:,}")
            with col2:
                st.metric("Database Size", stats["size"])
        
        st.divider()
        
        # Get all tables
        tables = get_all_tables()
        
        # Create expanders for each table
        for table in tables:
            with st.expander(f"📋 {table}"):
                # Show column information
                columns = get_table_schema(table)
                st.write("**Columns:**")
                for col in columns:
                    col_name, col_type, is_nullable, default = col
                    nullable_text = "NULL" if is_nullable == "YES" else "NOT NULL"
                    st.text(f"▫️ {col_name} ({col_type}) {nullable_text}")
                
                # Show sample data
                st.write("**Sample Data:**")
                preview = get_table_preview(table, limit=3)
                if preview:
                    df_preview = pd.DataFrame(preview)
                    st.dataframe(df_preview, use_container_width=True)
        
        # Show relationships in a separate expander
        with st.expander("🔗 Table Relationships"):
            relationships = get_table_relationships()
            for rel in relationships:
                st.text(f"{rel[1]}.{rel[2]} ➜ {rel[4]}.{rel[5]}")
    
    # Main area
    #st.write("### Ask questions about your database")
    st.write(f"### Ask questions about {db_name}") 
    st.write("Examples:")
    st.info("""
    - Show total revenue by category
    - Which products have the highest sales quantity?
    - List top 5 customers by order value
    """)
    
    # User input
    user_question = st.text_input("Enter your question:")
    
    if st.button("Get Answer", type="primary"):
        if user_question:
            with st.spinner("Processing your question..."):
                # Process the question
                sql_query, results, nl_response = process_question(user_question)
                
                # Display results in columns
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("### Generated SQL")
                    st.code(sql_query, language="sql")
                
                with col2:
                    st.markdown("### Results")
                    if results:
                        # Convert results to DataFrame
                        df = pd.DataFrame(results)
                        
                        # Format currency columns
                        currency_columns = [col for col in df.columns 
                                         if any(x in col.lower() for x in 
                                              ['price', 'revenue', 'total', 'amount', 'value'])]
                        
                        # Create a copy for display
                        df_display = df.copy()
                        
                        # Format currency columns
                        for col in currency_columns:
                            df_display[col] = df[col].apply(format_currency)
                        
                        # Display as a styled table
                        st.dataframe(
                            df_display,
                            use_container_width=True,
                            hide_index=True
                        )
                        
                        # Add download button
                        st.download_button(
                            "📥 Download Results",
                            df.to_csv(index=False).encode('utf-8'),
                            "query_results.csv",
                            "text/csv",
                            key='download-csv'
                        )
                    else:
                        st.info("No results found")
                
                # Display natural language response
                st.markdown("### Answer")
                st.write(nl_response)

if __name__ == "__main__":
    main()