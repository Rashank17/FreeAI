from freeai_agent.agent import FreeAIAgent
from freeai_agent.memory import MemoryStore
from freeai_agent.models import Source


class FakeSearch:
    def search(self, question: str):
        return [
            Source(title="A", url="https://example.com/a", snippet="Cats are mammals and pets."),
            Source(title="B", url="https://example.org/b", snippet="Cats are domesticated mammals."),
            Source(title="C", url="https://example.com/c", snippet="Duplicate domain should be removed."),
        ]


def test_answer_uses_multiple_sources_and_memory(tmp_path):
    memory = MemoryStore(db_path=str(tmp_path / "mem.db"))
    agent = FreeAIAgent(memory=memory, search=FakeSearch())

    first = agent.answer("s1", "What is a cat?")
    assert "Fused answer" in first.answer
    assert len(first.sources) == 2

    second = agent.answer("s1", "And are they good pets?")
    assert second.context_used


def test_revision(tmp_path):
    memory = MemoryStore(db_path=str(tmp_path / "mem.db"))
    agent = FreeAIAgent(memory=memory, search=FakeSearch())
    agent.answer("s2", "What is a cat?")
    revised = agent.revise_last_answer("s2", "Make it shorter")
    assert "Revised answer" in revised
