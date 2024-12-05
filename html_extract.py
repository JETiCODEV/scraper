import re
import asyncio
import json
import os
import markdownify

from typing import List
from dotenv import load_dotenv
from playwright.async_api import Page, async_playwright
from models import Element, StrippedElement
from settings import output_folder
from tools import count_tokens

# Load the default .env file
load_dotenv(dotenv_path=".env")

# Load the .env.local file (will override variables from .env if duplicated)
load_dotenv(dotenv_path=".env.local", override=True)

with open("inject.js", "r") as file:
    javascript = file.read()


def minify_elements(elements: List[StrippedElement], x: int) -> str:
    """
    Convert a list of Element objects to a minified JSON string.

    Args:
        elements (List[Element]): A list of Element objects.

    Returns:
        str: A minified JSON string representation of the elements.
    """
    # Convert the list of Element objects to a list of dictionaries
    elements_dict = [element.model_dump(exclude_none=True) for element in elements]

    # Minify the JSON
    minified_json = json.dumps(elements_dict, separators=(",", ":"))

    with open(
        os.path.join(output_folder, f"interactive_elements_minified_{x}.json"), "w"
    ) as file:
        file.write(minified_json)

    return minified_json


def prepare_elements(elements: List[Element], x: int) -> List[StrippedElement]:
    """
    Prepares a list of elements by converting them into `StrippedElement` objects
    and then minifies the resulting list based on a specified size.

    Args:
        elements (List[Element]): A list of `Element` objects to be processed.
        x (int): The maximum number of elements to retain after minification.

    Returns:
        List[StrippedElement]: A minified list of `StrippedElement` objects.
    """

    prepared_elements = [
        StrippedElement(
            id=element.id,
            tag=element.tag,
            ariaLabel=element.ariaLabel,
            innerText=element.innerText,
        )
        for element in elements
    ]

    return minify_elements(prepared_elements, x)


async def extract_markdown(page: Page, x: int, limit: int = None) -> str:
    """
    Extracts markdown content from a given web page asynchronously.

    Args:
        page (Page): A Playwright `Page` object representing the web page to extract content from.
        x (int): A parameter used to specify an aspect of the extraction logic (e.g., the section to extract or a specific selector index).
        limit (int, optional): The maximum number of characters to extract. Defaults to None, which implies no limit.

    Returns:
        str: The extracted markdown content as a string.
    """
    # Get the page content as HTML
    content = await page.content()
    content = re.sub(r"<script[^>]*>.*?</script>", "", content, flags=re.DOTALL)
    content = re.sub(r'\sclass="[^"]*"', '', content)

    # Convert HTML content to Markdown
    markdown = markdownify.markdownify(
        content,
        heading_style=markdownify.ASTERISK  # Compact heading style
    )

    # Minimize whitespace and reduce empty lines > 3 to 2
    markdown = re.sub(r'\n{4,}', '\n\n', markdown).strip()  # Collapse 4 or more newlines to 2

    # Ensure the data directory exists
    os.makedirs(output_folder, exist_ok=True)

    # Save the Markdown to a file
    file_path = os.path.join(output_folder, f"{x}.md")
    with open(file_path, "w", encoding="utf-8") as file:
        file.write(markdown)

    return markdown


async def extract_elements(page: Page, x: int) -> List[Element]:
    await page.wait_for_load_state("networkidle")
    await page.wait_for_load_state("domcontentloaded")
    await page.wait_for_load_state("load")

    # Extract interactive elements
    elements = await page.evaluate(javascript)

    output_file = f"interactive_elements_{x}.json"

    # Take a screenshot
    print("write screenshot")
    await page.screenshot(path=os.path.join(output_folder, "screenshot.jpeg"))

    await page.evaluate(""" () => {
         if (window.highlightcontainer) {
            window.highlightcontainer.remove();
            delete window.highlightcontainer;
        }
    }""")

    # Write to a JSON file
    with open(os.path.join(output_folder, output_file), "w", encoding="utf-8") as f:
        json.dump(elements, f, indent=4, ensure_ascii=False)

    print(f"Interactive elements dumped to {output_file}")

    # Convert elements to Element objects
    element_objects = [
        Element(
            id=element["id"],
            tag=element["tag"],
            idAttr=element.get("idAttr"),
            ariaLabel=element.get("ariaLabel"),
            innerText=element.get("innerText"),
            selector=element.get("selector"),
        )
        for element in elements
    ]

    # Convert the list of Element objects to a list of dictionaries
    elements_dict = [
        element.model_dump(exclude_none=True) for element in element_objects
    ]

    with open(
        os.path.join(output_folder, f"interactive_elements_{x}.json"), "w"
    ) as file:
        json.dump(elements_dict, file, indent=4, ensure_ascii=False)

    return element_objects


async def dump_interactive_elements(url):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        await page.goto(url)

        await page.wait_for_load_state("networkidle")
        await page.wait_for_load_state("domcontentloaded")

        await extract_elements(page, 999)    
        
        md = await extract_markdown(page, 999)
        
        print(count_tokens(md))

        input('press any key to continue')
        await browser.close()


if __name__ == "__main__":
    asyncio.run(dump_interactive_elements("https://www.standaard.be/"))
