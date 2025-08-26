from agent.agent import Agent


example_queries = ["Produce a head to head comparison of Charizard and Blastoise.",
                   "What are the type advantages and disadvantages of Electric and Ground types?",
                   "What are the base stats and abilities of Mewtwo?",
                   "Which Pokemon that lives near the sea is easiest to catch in Sapphire?"]

for query in example_queries:
    print(f"\n\n=== QUERY: {query} ===")
    agent = Agent(model="gpt-4o-mini", max_steps=6, temperature=0.3, verbose=True)
    agent.run(query)
