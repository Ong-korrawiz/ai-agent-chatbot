from agents.base_agent import BaseAgent
from utils.common import ConfigUtils

if __name__ == "__main__":

    config = ConfigUtils.load_config()
    joker_agent = BaseAgent(
        model=config.get('model', 'gpt-4o-mini-2024-07-18'),
        temperature=config.get('temperature', 0.7),
        system_prompt="You are a funny AI assistant that tells jokes about programming and makes people laugh. "
    )

    response = joker_agent.invoke("Tell me a joke about Python programming.")
    print(f"Joke: {response}")