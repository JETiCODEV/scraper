import os
import shutil

import nest_asyncio
import tiktoken
from crewai.types.usage_metrics import UsageMetrics
from dotenv import load_dotenv

from settings import output_folder


def export_token_use(output: UsageMetrics):
    with open(os.path.join(output_folder, "token_use.txt"), "a") as file:
        file.write(output.model_dump_json() + "\n")


def setup():
    print("Deleting folder...")
    if os.path.exists(output_folder):
        shutil.rmtree(output_folder)
    os.makedirs(output_folder, exist_ok=True)
    nest_asyncio.apply()
    load_dotenv(dotenv_path=".env")
    load_dotenv(dotenv_path=".env.local", override=True)


def count_tokens(input_string: str) -> int:
    """
    Counts the number of tokens in a given string for the GPT-4 model.

    Args:
        input_string (str): The string to tokenize and count.

    Returns:
        int: The number of tokens.
    """
    # Load the encoding for GPT-4
    encoding = tiktoken.encoding_for_model("gpt-4")

    # Encode the input string into tokens
    tokens = encoding.encode(input_string)

    # Return the count of tokens
    return len(tokens)
