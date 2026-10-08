"""Experiment 11: LangChain prompt-context growth. See framework_examples/README.md."""
from langchain_core.runnables import RunnableLambda
from langchain_core.prompts import ChatPromptTemplate


def run():
    prompt = ChatPromptTemplate.from_messages([
        ('system', 'Use only this context: {context}'), ('human', '{question}')])
    items = ['relevant fact', 'noise A', 'noise B', 'noise C']
    chain = prompt | RunnableLambda(lambda p: len(p.to_string()))
    return [chain.invoke({'context': ' '.join(items[:k]), 'question': 'What is relevant?'})
            for k in range(1, 5)]


if __name__ == "__main__":
    print(run())
