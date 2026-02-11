from pymilvus import DataType, FieldSchema

collection_schema_dict: dict = {
    "description": "MulvesDB collection schema for storing PDF document chunks and their embeddings",
    "name": "test",
    "fields": [
        FieldSchema(
            name="id",
            dtype=DataType.INT64,
            is_primary=True,
            auto_id=True
        ),
        FieldSchema(
            name="vector_id",
            dtype=DataType.VARCHAR,
            max_length=100
        ),
        FieldSchema(
            name="content",
            dtype=DataType.VARCHAR,
            max_length=65535
        ),
        FieldSchema(
            name="embedding",
            dtype=DataType.FLOAT_VECTOR,
            dim=1536
        ),
        FieldSchema(
            name="page_number",
            dtype=DataType.INT64
        ),
        FieldSchema(
            name="chunk_index",
            dtype=DataType.INT64
        ),
        FieldSchema(
            name="document_id",
            dtype=DataType.INT64
        ),
        FieldSchema(
            name="metadata",
            dtype=DataType.JSON
        )
    ]
}
