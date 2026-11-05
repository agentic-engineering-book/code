"""Experiment 19: Compress working context in LangChain. See README."""
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableLambda

from agentic.live import schema
from framework_examples.support import chat

TRANSCRIPT = """\
user: Hi! Hope your week is going well.
assistant: It is, thanks. What can I do for you?
user: I need a technical report on our caching layer, under 500 words.
assistant: Who is the audience?
user: The platform engineers. Oh, and sending anything by email needs my \
approval first.
assistant: Understood. Searching for sources.
tool: search S1 failed: timeout
tool: search S2 failed: no results
tool: search S3 returned the caching design document
assistant: I found the design document (S3).
user: Great, cite S3 in the report. By the way, did you see the game?
assistant: I did not, but I hear it was close.
user: It was! Anyway, email the report to the platform team when done."""
TOOLS = [schema("send_email", "Send an email.", to="the recipient"),
         schema("ask_approval", "Ask the user to approve an action.",
                action="the action to approve")]
COMPRESSORS = {
    "FULL": lambda text: text,
    "LAST_SIX": lambda text: "\n".join(text.splitlines()[-6:]),  # window
}


def run():
    model = chat().bind_tools(
        [{"type": "function", "function": t} for t in TOOLS],
        tool_choice="required", parallel_tool_calls=False)
    prompt = ChatPromptTemplate.from_messages([
        ("system", "Conversation so far:\n{context}"),
        ("human", "The report is finished. Take the next step.")])
    lines = []
    for name, compress in COMPRESSORS.items():
        chain = (RunnableLambda(lambda t, c=compress: {"context": c(t)})
                 | prompt | model)
        replies = chain.batch([TRANSCRIPT] * 3)
        kept = len(compress(TRANSCRIPT))
        lines.append(f"{name}: {kept} of {len(TRANSCRIPT)} characters")
        lines.append("  next step: " + ", ".join(
            r.tool_calls[0]["name"] for r in replies))
    return lines


if __name__ == "__main__":
    for line in run():
        print(line)
