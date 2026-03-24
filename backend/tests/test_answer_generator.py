# backend/tests/test_answer_generator.py
import importlib
import pytest
from unittest.mock import Mock, patch


@pytest.fixture(autouse=True)
def reset_answer_generator_singleton():
    """Reset answer generator singleton before and after each test"""
    answer_gen_module = importlib.import_module("core.answer_generator")
    answer_gen_module._answer_generator = None
    yield
    answer_gen_module._answer_generator = None


def test_answer_generator_initializes(mock_settings):
    """Test answer generator initializes successfully"""
    with patch('core.answer_generator.get_groq_client') as mock_groq:
        mock_groq.return_value = Mock()
        from core.answer_generator import get_answer_generator

        generator = get_answer_generator()

        assert generator is not None
        mock_groq.assert_called_once()


def test_answer_generator_singleton(mock_settings):
    """Test answer generator returns same instance"""
    with patch('core.answer_generator.get_groq_client') as mock_groq:
        mock_groq.return_value = Mock()
        from core.answer_generator import get_answer_generator

        gen1 = get_answer_generator()
        gen2 = get_answer_generator()

        assert gen1 is gen2
        mock_groq.assert_called_once()


def test_generate_answer_with_results(mock_settings):
    """Test generating answer with valid results"""
    with patch('core.answer_generator.get_groq_client') as mock_groq:
        mock_client = Mock()
        mock_client.chat_completion.return_value = (
            "There are 3 people involved in drug crimes: John Smith, Sarah Jones, and Mike Brown."
        )
        mock_groq.return_value = mock_client

        from core.answer_generator import get_answer_generator

        generator = get_answer_generator()
        question = "Find people involved in drug crimes"
        cypher = "MATCH (p:Person)-[:PARTY_TO]->(c:Crime) WHERE toLower(c.type) CONTAINS 'drug' RETURN p.name, p.surname"
        results = [
            {"p.name": "John", "p.surname": "Smith"},
            {"p.name": "Sarah", "p.surname": "Jones"},
            {"p.name": "Mike", "p.surname": "Brown"}
        ]

        answer = generator.generate(question, cypher, results)

        assert answer == "There are 3 people involved in drug crimes: John Smith, Sarah Jones, and Mike Brown."
        mock_client.chat_completion.assert_called_once()


def test_generate_answer_with_empty_results(mock_settings):
    """Test generating answer when no results found"""
    with patch('core.answer_generator.get_groq_client') as mock_groq:
        mock_client = Mock()
        mock_groq.return_value = mock_client

        from core.answer_generator import get_answer_generator

        generator = get_answer_generator()
        question = "Find people involved in spaceship crimes"
        cypher = "MATCH (p:Person)-[:PARTY_TO]->(c:Crime) WHERE toLower(c.type) CONTAINS 'spaceship' RETURN p.name"
        results = []

        answer = generator.generate(question, cypher, results)

        # Should return helpful message without calling LLM
        assert "No results were found" in answer
        assert "spaceship crimes" in answer
        mock_client.chat_completion.assert_not_called()


def test_generate_answer_with_count_result(mock_settings):
    """Test generating answer with aggregation/count result"""
    with patch('core.answer_generator.get_groq_client') as mock_groq:
        mock_client = Mock()
        mock_client.chat_completion.return_value = (
            "There are 42 crimes recorded in the database."
        )
        mock_groq.return_value = mock_client

        from core.answer_generator import get_answer_generator

        generator = get_answer_generator()
        question = "How many crimes are recorded?"
        cypher = "MATCH (c:Crime) RETURN count(c) AS total_crimes"
        results = [{"total_crimes": 42}]

        answer = generator.generate(question, cypher, results)

        assert "42 crimes" in answer.lower() or "42" in answer
        mock_client.chat_completion.assert_called_once()


def test_format_results_single_value(mock_settings):
    """Test formatting single value result"""
    with patch('core.answer_generator.get_groq_client') as mock_groq:
        mock_groq.return_value = Mock()
        from core.answer_generator import AnswerGenerator

        generator = AnswerGenerator()
        results = [{"count": 10}]

        formatted = generator._format_results(results)

        assert formatted == "count: 10"


def test_format_results_multiple_rows(mock_settings):
    """Test formatting multiple result rows"""
    with patch('core.answer_generator.get_groq_client') as mock_groq:
        mock_groq.return_value = Mock()
        from core.answer_generator import AnswerGenerator

        generator = AnswerGenerator()
        results = [
            {"name": "John", "age": "34"},
            {"name": "Sarah", "age": "28"},
            {"name": "Mike", "age": "45"}
        ]

        formatted = generator._format_results(results)

        assert "1. name: John, age: 34" in formatted
        assert "2. name: Sarah, age: 28" in formatted
        assert "3. name: Mike, age: 45" in formatted


def test_format_results_truncates_large_results(mock_settings):
    """Test formatting truncates results beyond 50 rows"""
    with patch('core.answer_generator.get_groq_client') as mock_groq:
        mock_groq.return_value = Mock()
        from core.answer_generator import AnswerGenerator

        generator = AnswerGenerator()
        # Create 60 results
        results = [{"id": i, "name": f"Person{i}"} for i in range(60)]

        formatted = generator._format_results(results)

        # Should show first 50 and mention truncation
        assert "1. id: 0" in formatted
        assert "50. id: 49" in formatted
        assert "10 more results not shown" in formatted


def test_format_results_empty(mock_settings):
    """Test formatting empty results"""
    with patch('core.answer_generator.get_groq_client') as mock_groq:
        mock_groq.return_value = Mock()
        from core.answer_generator import AnswerGenerator

        generator = AnswerGenerator()
        results = []

        formatted = generator._format_results(results)

        assert formatted == "No results found"


def test_build_system_prompt(mock_settings):
    """Test system prompt contains required instructions"""
    with patch('core.answer_generator.get_groq_client') as mock_groq:
        mock_groq.return_value = Mock()
        from core.answer_generator import AnswerGenerator

        generator = AnswerGenerator()
        system_prompt = generator._build_system_prompt()

        assert "crime investigation analyst" in system_prompt.lower()
        assert "clear" in system_prompt.lower()
        assert "concise" in system_prompt.lower()
        assert "do not mention cypher" in system_prompt.lower() or "without mentioning" in system_prompt.lower()


def test_build_user_prompt(mock_settings):
    """Test user prompt contains all required components"""
    with patch('core.answer_generator.get_groq_client') as mock_groq:
        mock_groq.return_value = Mock()
        from core.answer_generator import AnswerGenerator

        generator = AnswerGenerator()
        question = "How many crimes?"
        cypher = "MATCH (c:Crime) RETURN count(c)"
        results = [{"count": 10}]

        user_prompt = generator._build_user_prompt(question, cypher, results)

        assert question in user_prompt
        assert cypher in user_prompt
        assert "count: 10" in user_prompt


def test_generate_empty_result_answer(mock_settings):
    """Test empty result answer is helpful"""
    with patch('core.answer_generator.get_groq_client') as mock_groq:
        mock_groq.return_value = Mock()
        from core.answer_generator import AnswerGenerator

        generator = AnswerGenerator()
        question = "Find unicorn crimes"

        answer = generator._generate_empty_result_answer(question)

        assert "no results" in answer.lower()
        assert question in answer
        assert "try" in answer.lower() or "could mean" in answer.lower()
