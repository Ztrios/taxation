import uuid

from services.agent import tax_agent_graph


def run_cli():
    """
    Simple terminal chat loop that routes through the tax filter agent.
    Keeps a single session_id for the CLI run so history is preserved.
    """
    session_id = str(uuid.uuid4())
    print("Tax Filter Agent CLI")
    print("Type 'exit' to quit.\n")

    while True:
        user_input = input("You: ").strip()
        if user_input.lower() in {"exit", "quit"}:
            print("Exiting.")
            break
        if not user_input:
            continue

        state = {
            "user_query": user_input,
            "session_id": session_id,
        }

        result = tax_agent_graph.invoke(state)
        is_relevant = result.get("is_relevant")
        final_response = result.get("final_response", "")

        print(f"[Filter] Tax-related: {is_relevant}")
        print(f"Assistant: {final_response}\n")


if __name__ == "__main__":
    run_cli()

