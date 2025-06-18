from abc import ABC, abstractmethod


class VectorStoreBase(ABC):
    @abstractmethod
    async def create_col(self, name, vector_size, distance):
        """Create a new collection."""
        pass

    @abstractmethod
    async def insert(self, vectors, payloads=None, ids=None):
        """Insert vectors into a collection."""
        pass

    @abstractmethod
    async def search(self, query, vectors, limit=5, filters=None):
        """Search for similar vectors."""
        pass

    @abstractmethod
    async def delete(self, vector_id):
        """Delete a vector by ID."""
        pass

    @abstractmethod
    async def update(self, vector_id, vector=None, payload=None):
        """Update a vector and its payload."""
        pass

    @abstractmethod
    async def get(self, vector_id):
        """Retrieve a vector by ID."""
        pass

    @abstractmethod
    async def list_cols(self):
        """List all collections."""
        pass

    @abstractmethod
    async def delete_col(self):
        """Delete a collection."""
        pass

    @abstractmethod
    async def col_info(self):
        """Get information about a collection."""
        pass

    @abstractmethod
    async def list(self, filters=None, limit=None):
        """List all memories."""
        pass
    
    @abstractmethod
    async def reset(self):
        """Reset by delete the collection and recreate it."""
        pass
