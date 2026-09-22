import pytest

from rag.embeddings import EmbeddingsAdapter

pytestmark = pytest.mark.gemma


def test_gemma_document_vector_has_the_model_dimension():
    vectors = EmbeddingsAdapter().embed(
        ["Employees must offer the neighboring pod some cake."], task="document"
    )
    assert len(vectors) == 1
    assert len(vectors[0]) == 768
