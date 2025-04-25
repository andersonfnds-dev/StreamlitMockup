from pymongo import MongoClient
import streamlit as st

@st.cache_resource
def get_mongo_client():
    """
    Establish a connection to the MongoDB database.
    The connection is cached to avoid reconnecting on every Streamlit rerun.

    Returns:
        MongoClient: A MongoDB client instance.
    """
    uri = "mongodb+srv://antea_ehs:<120r4l4VjzQesJGb>@dlh-ai.1gw1u.mongodb.net/?retryWrites=true&w=majority&appName=DLH-AI"
    try:
        client = MongoClient(uri)
        return client
    except Exception as e:
        st.error(f"Failed to connect to MongoDB: {e}")
        return None

def get_database(client):
    """
    Get the 'antea_ehs_metadata' database from the MongoDB client.

    Args:
        client (MongoClient): The MongoDB client instance.

    Returns:
        Database: The MongoDB database instance.
    """
    try:
        return client["antea_ehs_metadata"]
    except Exception as e:
        st.error(f"Failed to access database 'ehs_register': {e}")
        return None