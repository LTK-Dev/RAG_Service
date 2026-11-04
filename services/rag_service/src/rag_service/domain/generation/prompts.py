from string import Template


RAG_PROMPT_TEMPLATE = Template(
    """You are a helpful assistant. Answer the user's question based only on the context provided below.

Context from the documents:
--- CONTEXT ---
$context
--- END CONTEXT ---

User Question: $question""",
)
