def get_prompt(txt_path: str, **kwargs) -> str:
    """
    Reads a prompt from a text file and formats it with the provided keyword arguments.

    Args:
        txt_path (str): Path to the text file containing the prompt.
        **kwargs: Keyword arguments to format the prompt.

    Returns:
        str: The formatted prompt.
    """
    with open(txt_path, 'r', encoding='utf-8') as file:
        prompt = file.read()
    
    return prompt.format(**kwargs) if kwargs else prompt
