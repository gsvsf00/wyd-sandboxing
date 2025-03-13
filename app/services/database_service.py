#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Database Service for WydBot.
Handles MongoDB connectivity and database operations.
"""

import pymongo
from pymongo.errors import ConnectionFailure, OperationFailure, ServerSelectionTimeoutError
from typing import Dict, Any, List, Optional, Union
import time
import threading
from bson.objectid import ObjectId
import os
import logging
from datetime import datetime
import sys
import tkinter as tk

# Import utilities
from app.utils.logger import LoggerWrapper
from app.utils.config import get_config_value

# Global logger instance
logger = LoggerWrapper(name="database_service")

# Define a custom exception for database connection failures
class DatabaseConnectionError(Exception):
    """
    Exception raised when a database connection fails and the app is not configured to use a mock database.
    """
    def __init__(self, message="Failed to connect to MongoDB"):
        self.message = message
        super().__init__(self.message)

class MockCollection:
    """Mock collection for development when MongoDB is not available."""
    def __init__(self, name):
        self.name = name
        self.data = []
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"Initialized mock collection: {name}")
    
    def insert_one(self, document):
        """Insert a document into the collection."""
        if "_id" not in document:
            document["_id"] = len(self.data) + 1
        document["created_at"] = datetime.now()
        document["updated_at"] = datetime.now()
        self.data.append(document)
        self.logger.info(f"Inserted document into {self.name}: {document}")
        return {"inserted_id": document["_id"]}
    
    def find_one(self, filter=None, **kwargs):
        """Find a document in the collection."""
        query = filter or {}
        self.logger.info(f"Finding document in {self.name} with query: {query}")
        for doc in self.data:
            match = True
            for key, value in query.items():
                if key not in doc or doc[key] != value:
                    match = False
                    break
            if match:
                self.logger.info(f"Found document: {doc}")
                return doc
        self.logger.info("No document found")
        return None
    
    def find(self, filter=None, **kwargs):
        """Find documents in the collection."""
        query = filter or {}
        self.logger.info(f"Finding documents in {self.name} with query: {query}")
        results = []
        for doc in self.data:
            match = True
            for key, value in query.items():
                if key not in doc or doc[key] != value:
                    match = False
                    break
            if match:
                results.append(doc)
        self.logger.info(f"Found {len(results)} documents")
        return results
    
    def update_one(self, query, update):
        """Update a document in the collection."""
        self.logger.info(f"Updating document in {self.name} with query: {query}, update: {update}")
        for i, doc in enumerate(self.data):
            match = True
            for key, value in query.items():
                if key not in doc or doc[key] != value:
                    match = False
                    break
            if match:
                for key, value in update.get("$set", {}).items():
                    doc[key] = value
                doc["updated_at"] = datetime.now()
                self.data[i] = doc
                self.logger.info(f"Updated document: {doc}")
                return {"modified_count": 1}
        self.logger.info("No document found to update")
        return {"modified_count": 0}
    
    def delete_one(self, query):
        """Delete a document from the collection."""
        self.logger.info(f"Deleting document from {self.name} with query: {query}")
        for i, doc in enumerate(self.data):
            match = True
            for key, value in query.items():
                if key not in doc or doc[key] != value:
                    match = False
                    break
            if match:
                del self.data[i]
                self.logger.info(f"Deleted document")
                return {"deleted_count": 1}
        self.logger.info("No document found to delete")
        return {"deleted_count": 0}

class MockDatabase:
    """Mock database for development when MongoDB is not available."""
    def __init__(self):
        self.collections = {}
        self.logger = logging.getLogger(__name__)
        self.logger.info("Initialized mock database")
    
    def __getitem__(self, name):
        if name not in self.collections:
            self.collections[name] = MockCollection(name)
        return self.collections[name]

class DatabaseService:
    """
    Service for interacting with the MongoDB database.
    """
    
    def __init__(self, config=None):
        """
        Initialize the database service.
        
        Args:
            config: Database configuration
        """
        self.config = config or {}
        self.client = None
        self.db = None
        self.use_mock_db = self.config.get("use_mock_db", False)
        self.connection_string = self.config.get("connection_string", "")
        self.database_name = self.config.get("database_name", "wydbot")
        self.connect_timeout_ms = self.config.get("connect_timeout_ms", 5000)
        self.server_selection_timeout_ms = self.config.get("server_selection_timeout_ms", 5000)
        self.max_pool_size = self.config.get("max_pool_size", 50)
        self.logger = LoggerWrapper(name="database_service")
        
        # Initialize connection lock and retry parameters
        self.connection_lock = threading.Lock()
        self.connection_retries = 0
        self.max_retries = 3
        self.retry_delay = 2.0  # seconds
        self.is_connected = False
        
        # Initialize mock database if configured to use it
        if self.use_mock_db:
            self.logger.warning("Using mock database")
            self.db = MockDatabase()
            self.is_mock = True
            self.logger.info("Initialized mock database")
        else:
            self.logger.info("Using real MongoDB connection")
            self.is_mock = False
    
    def init(self, app_controller):
        """
        Initialize the database service with the app controller.
        
        Args:
            app_controller: Application controller instance
        """
        self.app_controller = app_controller
        
        # Connect to the database
        if not self.connect():
            self.logger.error("Failed to connect to MongoDB")
            
            if self.use_mock_db:
                self.logger.warning("Using mock database")
                self.db = MockDatabase()
            else:
                raise DatabaseConnectionError("Failed to connect to MongoDB")
        
        # Ensure indexes
        self._ensure_indexes()
        
        self.logger.info("Database service initialized")
        
    def cleanup(self):
        """Clean up database connections."""
        try:
        if self.client:
            self.client.close()
                self.logger.info("Database connection closed")
        except Exception as e:
            self.logger.error(f"Error closing database connection: {e}")
            
    def _ensure_indexes(self):
        """Ensure database indexes exist."""
        try:
            # Users collection
            users = self.db.users
            
            # Create username index as unique
            users.create_index("username", unique=True)
            
            try:
                # For email index, first try to fix any null email entries
                # by updating them to have unique placeholder values
                null_users = list(users.find({"email": None}))
                for i, user in enumerate(null_users):
                    users.update_one(
                        {"_id": user["_id"]},
                        {"$set": {"email": f"placeholder_{user['_id']}@example.com"}}
                    )
                
                # Then create the unique email index
                users.create_index("email", unique=True)
            except Exception as e:
                self.logger.warning(f"Could not create unique email index: {e}")
                # Create a non-unique index instead
                users.create_index("email", unique=False)
                self.logger.info("Created non-unique email index instead")
            
            # Other collections and indexes as needed
            
        except Exception as e:
            self.logger.error(f"Error creating database indexes: {e}", exc_info=True)
            
    def get_collection(self, name: str):
        """
        Get a collection by name.
        
        Args:
            name: Collection name
            
        Returns:
            Collection object or MockCollection if using mock database
        """
        try:
            if self.use_mock_db:
                return self.mock_db[name]
                
            # Check if database is available - use is None check instead of truth value
            if self.db is None:
                self.logger.warning("Database not connected, using mock collection")
                return self.mock_db[name]
                
            return self.db[name]
        except Exception as e:
            self.logger.error(f"Error getting collection {name}: {e}", exc_info=True)
            return self.mock_db[name]  # Fallback to mock
        
    def find_one(self, collection: str, query: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Find a single document in a collection.
        
        Args:
            collection: The collection name
            query: The query to execute
            
        Returns:
            The document, or None if not found
        """
        try:
            coll = self.get_collection(collection)
            if not coll:
                return None
                
            return coll.find_one(query)
            
        except Exception as e:
            self.logger.error(f"Error finding document in {collection}: {e}", exc_info=True)
            return None
            
    def find(self, collection: str, query: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Find documents in a collection.
        
        Args:
            collection: The collection name
            query: The query to execute
            
        Returns:
            List of documents, or empty list if none found
        """
        try:
            coll = self.get_collection(collection)
            if not coll:
                return []
                
            return list(coll.find(query))
            
        except Exception as e:
            self.logger.error(f"Error finding documents in {collection}: {e}", exc_info=True)
            return []
            
    def insert_one(self, collection: str, document: Dict[str, Any]) -> Optional[str]:
        """
        Insert a document into a collection.
        
        Args:
            collection: The collection name
            document: The document to insert
            
        Returns:
            The ID of the inserted document, or None if insertion failed
        """
        try:
            coll = self.get_collection(collection)
            if not coll:
                return None
                
            result = coll.insert_one(document)
            return str(result.inserted_id)
            
        except Exception as e:
            self.logger.error(f"Error inserting document into {collection}: {e}", exc_info=True)
            return None
            
    def update_one(self, collection: str, query: Dict[str, Any], update: Dict[str, Any]) -> bool:
        """
        Update a document in a collection.
        
        Args:
            collection: The collection name
            query: The query to find the document
            update: The update to apply
            
        Returns:
            True if update was successful, False otherwise
        """
        try:
            coll = self.get_collection(collection)
            if not coll:
                return False
                
            result = coll.update_one(query, update)
            return result.modified_count > 0
            
        except Exception as e:
            self.logger.error(f"Error updating document in {collection}: {e}", exc_info=True)
            return False
            
    def delete_one(self, collection: str, query: Dict[str, Any]) -> bool:
        """
        Delete a document from a collection.
        
        Args:
            collection: The collection name
            query: The query to find the document
            
        Returns:
            True if deletion was successful, False otherwise
        """
        try:
            coll = self.get_collection(collection)
            if not coll:
                return False
                
            result = coll.delete_one(query)
            return result.deleted_count > 0
            
        except Exception as e:
            self.logger.error(f"Error deleting document from {collection}: {e}", exc_info=True)
            return False
    
    def _mask_connection_string(self, uri: str) -> str:
        """
        Mask sensitive information in connection string for logging.
        
        Args:
            uri: MongoDB connection string
            
        Returns:
            Masked connection string
        """
        if not uri:
            return "None"
        
        try:
            # Simple masking for mongodb://user:pass@host:port/db format
            if '@' in uri:
                prefix, rest = uri.split('@', 1)
                if '//' in prefix and ':' in prefix:
                    protocol, auth = prefix.split('//', 1)
                    if ':' in auth:
                        user, _ = auth.split(':', 1)
                        return f"{protocol}//{user}:****@{rest}"
            
            # If we can't parse it properly, just return a generic masked string
            return uri.split('://')[0] + "://****"
        except Exception:
            return "mongodb://****"
    
    def connect(self) -> bool:
        """
        Connect to the MongoDB database.
        
        Returns:
            bool: True if connection was successful, False otherwise
        """
        if self.use_mock_db:
            return True  # Mock database is already "connected"
        
        try:
            if not self.connection_string:
                self.logger.error("No connection string provided for MongoDB")
                return False
            
            # Get SSL configuration from config
            ssl_enabled = self.config.get("ssl", True)
            tls_allow_invalid = self.config.get("tls_allow_invalid_certificates", True)
            
            # Create client with appropriate timeout settings and SSL configuration
            connection_params = {
                "connectTimeoutMS": self.connect_timeout_ms,
                "serverSelectionTimeoutMS": self.server_selection_timeout_ms,
                "maxPoolSize": self.max_pool_size,
                "tlsAllowInvalidCertificates": tls_allow_invalid
            }
            
            # Add SSL parameters if SSL is enabled
            if ssl_enabled:
                connection_params["tls"] = True
            
                self.client = pymongo.MongoClient(
                self.connection_string,
                **connection_params
                )
                
            # Test connection by accessing server info
            self.client.server_info()
                
                # Get database
            self.db = self.client[self.database_name]
                
            # Set up indexes
            self._ensure_indexes()
                
            self.logger.info(f"Connected to MongoDB database: {self.database_name}")
                return True
        except ConnectionFailure as e:
            self.logger.error(f"MongoDB connection failed: {e}")
            return False
        except ServerSelectionTimeoutError as e:
            self.logger.error(f"MongoDB server selection timeout: {e}")
            return False
        except OperationFailure as e:
            # This could be an authentication failure or insufficient permissions
            self.logger.error(f"MongoDB operation failed: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error connecting to MongoDB: {e}")
                return False
    
    def reconnect(self) -> bool:
        """
        Attempt to reconnect to the database.
        
        Returns:
            True if successful, False otherwise
        """
        with self.connection_lock:
            # Clean up existing connection
            if self.client:
                try:
                    self.client.close()
                except Exception:
                    pass
            
            self.client = None
            self.db = None
            self.is_connected = False
            
            # Increment retry counter
            self.connection_retries += 1
            
            # Check if max retries exceeded
            if self.connection_retries >= self.max_retries:
                logger.error(f"Maximum connection retries ({self.max_retries}) exceeded")
                return False
            
            # Wait before retry
            time.sleep(self.retry_delay)
            
            # Update SSL settings to be more permissive
            self.config["ssl"] = True
            self.config["tls_allow_invalid_certificates"] = True
            
            # Try to connect again
            return self.connect()
    
    def check_health(self) -> bool:
        """
        Check if the database connection is healthy.
        
        Returns:
            True if healthy, False otherwise
        """
        if self.use_mock_db:
            return True  # Mock database is always "healthy"
        
        if not self.client:
            return False
        
        try:
            # Ping the database
            self.client.admin.command('ping')
            self.is_connected = True
            return True
        except pymongo.errors.ServerSelectionTimeoutError as e:
            self.logger.error(f"Database health check failed: {e}")
            self.is_connected = False
            
            # Try to reconnect with updated SSL settings
            if "SSL" in str(e) or "TLS" in str(e):
                self.logger.warning("SSL/TLS error detected, attempting to reconnect with updated settings")
                return self.reconnect()
            
            return False
        except Exception as e:
            self.logger.error(f"Database health check failed: {e}")
            self.is_connected = False
            return False
    
    def _ensure_connected(self) -> bool:
        """
        Ensure the database is connected.
        
        Returns:
            True if connected, False otherwise
        """
        if self.is_connected:
            return True
        
        return self.connect()
    
    def find_by_id(
        self,
        collection_name: str,
        document_id: Union[str, ObjectId],
        projection: Dict = None
    ) -> Optional[Dict]:
        """
        Find a document by its ID.
        
        Args:
            collection_name: Name of the collection
            document_id: Document ID (string or ObjectId)
            projection: Projection specification
            
        Returns:
            Document or None if not found
        """
        if isinstance(document_id, str):
            try:
                document_id = ObjectId(document_id)
            except Exception:
                logger.error(f"Invalid ObjectId: {document_id}")
                return None
        
        return self.find_one(
            collection_name,
            {"_id": document_id},
            projection
        )
    
    def insert_many(
        self,
        collection_name: str,
        documents: List[Dict]
    ) -> Optional[List[str]]:
        """
        Insert multiple documents into a collection.
        
        Args:
            collection_name: Name of the collection
            documents: Documents to insert
            
        Returns:
            List of inserted IDs or None if failed
        """
        if not self._ensure_connected():
            return None
        
        try:
            collection = self.get_collection(collection_name)
            result = collection.insert_many(documents)
            
            if result.acknowledged:
                return [str(id) for id in result.inserted_ids]
            else:
                logger.warning(f"Insert many in {collection_name} not acknowledged")
                return None
            
        except Exception as e:
            logger.error(f"Error inserting documents in {collection_name}: {e}")
            return None
    
    def update_many(
        self,
        collection_name: str,
        query: Dict,
        update: Dict,
        upsert: bool = False
    ) -> Optional[Dict]:
        """
        Update multiple documents in a collection.
        
        Args:
            collection_name: Name of the collection
            query: Query filter
            update: Update operations
            upsert: Whether to insert if not found
            
        Returns:
            Update result or None if failed
        """
        if not self._ensure_connected():
            return None
        
        try:
            collection = self.get_collection(collection_name)
            result = collection.update_many(
                filter=query,
                update=update,
                upsert=upsert
            )
            
            if result.acknowledged:
                return {
                    "matched_count": result.matched_count,
                    "modified_count": result.modified_count,
                    "upserted_id": str(result.upserted_id) if result.upserted_id else None
                }
            else:
                logger.warning(f"Update many in {collection_name} not acknowledged")
                return None
            
        except Exception as e:
            logger.error(f"Error updating documents in {collection_name}: {e}")
            return None
    
    def delete_many(
        self,
        collection_name: str,
        query: Dict
    ) -> Optional[int]:
        """
        Delete multiple documents from a collection.
        
        Args:
            collection_name: Name of the collection
            query: Query filter
            
        Returns:
            Number of deleted documents or None if failed
        """
        if not self._ensure_connected():
            return None
        
        try:
            collection = self.get_collection(collection_name)
            result = collection.delete_many(filter=query)
            
            if result.acknowledged:
                return result.deleted_count
            else:
                logger.warning(f"Delete many in {collection_name} not acknowledged")
                return None
            
        except Exception as e:
            logger.error(f"Error deleting documents in {collection_name}: {e}")
            return None
    
    def count(
        self,
        collection_name: str,
        query: Dict = None
    ) -> Optional[int]:
        """
        Count documents in a collection.
        
        Args:
            collection_name: Name of the collection
            query: Query filter
            
        Returns:
            Document count or None if failed
        """
        if not self._ensure_connected():
            return None
        
        try:
            collection = self.get_collection(collection_name)
            return collection.count_documents(filter=query or {})
            
        except Exception as e:
            logger.error(f"Error counting documents in {collection_name}: {e}")
            return None
    
    def aggregate(
        self,
        collection_name: str,
        pipeline: List[Dict]
    ) -> List[Dict]:
        """
        Perform an aggregation on a collection.
        
        Args:
            collection_name: Name of the collection
            pipeline: Aggregation pipeline
            
        Returns:
            Aggregation results
        """
        if not self._ensure_connected():
            return []
        
        try:
            collection = self.get_collection(collection_name)
            return list(collection.aggregate(pipeline))
            
        except Exception as e:
            logger.error(f"Error performing aggregation on {collection_name}: {e}")
            return []
    
    def shutdown(self):
        """Shut down the database service safely."""
        try:
            with self.connection_lock:
                if self.client and not self.is_mock:
                    self.logger.info("Closing database connection")
                    self.client.close()
                    self.client = None
                self.is_connected = False
                self.logger.info("Database connection closed")
        except Exception as e:
            self.logger.error(f"Error closing database connection: {str(e)}")
    
    def is_healthy(self) -> bool:
        """
        Check if the database service is healthy.
        
        Returns:
            True if healthy, False otherwise
        """
        if self.use_mock_db:
            logger.warning("Using mock database")
            return True
            
        if not self.is_connected:
            return False
            
        try:
            # Ping the database
            self.client.admin.command("ping")
            return True
        except Exception as e:
            logger.error(f"Database health check failed: {str(e)}")
            return False 