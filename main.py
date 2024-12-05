import asyncio

from crewai.tools import tool
from crewai import LLM, Agent, Crew, Process, Task
from playwright.async_api import async_playwright

from html_extract import (
    extract_elements,
    extract_markdown,
    prepare_elements,
)
from models import TaskList
from tools import setup, export_token_use

groq_vision_90b = "groq/llama-3.2-90b-vision-preview"
gemini_flash_15 = "gemini/gemini-1.5-flash"

planner_llm = LLM(model=gemini_flash_15, temperature=0, verbose=True)
scraper_llm = LLM(model=groq_vision_90b, temperature=0, verbose=True)
extract_llm = LLM(model=gemini_flash_15, temperature=0, verbose=True)

# Tools
@tool("Interact with an element on a page")
def interact_with_element(id: int, arguments: str = "") -> str:
    """
    Interacts with a specified element on a webpage using its ID.

    Args:
        id (int): The ID of the element to interact with.
        arguments (str, optional): The input value for the interaction. Defaults to an empty string ("").
            - For `input` elements, this value is used to fill the input field.
            - For other elements (e.g., buttons, links), this value is ignored.

    Returns:
        str: A confirmation message ("DONE") upon successful interaction.

    Raises:
        ValueError: If the element has an unsupported tag or if `arguments` is not provided for an `input` tag.
    """
    global elements, page

    element = elements[id]

    locator = page.locator(element.selector)

    async def async_interact():
        if element.tag in ["button", "a"]:
            await locator.click()
        elif element.tag == "input":
            if not arguments:
                raise ValueError("Input elements require arguments.")
            await locator.fill(arguments)
        else:
            raise ValueError(f"Unsupported tag: {element.tag}")

    loop = asyncio.get_event_loop()
    loop.run_until_complete(async_interact())

    return "DONE"


# Planner agent setup


planner_agent = Agent(
    llm=planner_llm,
    goal=(
        "Create a step-by-step task list on how you can achieve the requested task. "
        "Consider that most web pages have a cookie consent, which should be a separate step. "
        "Always focus on interacting with the search functionality to reach a goal unless the user asked not to! "
        "Skip the navigate to page step"
        "When doing a search put the clicking on the search functionality, entering the search string and potentially clicking on search into separate steps"
        "When doing a search expect that after entering the search string and/or clicking search the search results appear and should be picked from the list."
        "Use these user guidelines: {plan_guide}"
        "The output should be in json and contain the following properties: Nr, Task, Outcome"
    ),
    role="an expert web interaction planner",
    backstory="Based on a task you think about which steps should be needed to achieve a task.",
    verbose=True
)

plan_task = Task(
    description="{user_question}",
    agent=planner_agent,
    expected_output="Json list containing each task & outcome.",
    output_pydantic=TaskList,
)

plan_crew = Crew(
    agents=[planner_agent], tasks=[plan_task], process=Process.sequential, verbose=True
)

# Execution crew

page_scrape_agent = Agent(
    llm=scraper_llm,
    goal="Identify the most relevant element in the provided element list to achieve the given task. Return its ID and, if applicable, any required arguments for interacting with the element. Make sure that the returned data is available in the 'Elements list'!",
    role="Element interaction analyzer tasked with selecting the optimal element ID and, where relevant, suggesting interaction arguments for input elements.",
    backstory="You are an expert in analyzing webpage elements and identifying the best element to interact with to complete a task.",
    verbose=True,
)

page_scrape_task = Task(
    description="""
    Task: {task}
    
    Previous executed task: {previous}
    
    Element list: {elements}
    """,
    agent=page_scrape_agent,
    expected_output="id: number, arguments: optional string when input",
)

page_execute_agent = Agent(
    llm=planner_llm,
    goal="Execute an element interaction",
    role="Element interactor",
    backstory="You are an expert in using the provided tools",
    tools=[interact_with_element],
    verbose=True,
)

page_execute_task = Task(
    description="""Execute the given element interaction""",
    agent=page_execute_agent,
    expected_output="OK if it succeeded NOT_FOUND if there is no element found",
)

interact_crew = Crew(
    agents=[page_scrape_agent, page_execute_agent],
    tasks=[page_scrape_task, page_execute_task],
    process=Process.sequential,
    verbose=True,
)

######

# execution crew

extract_agent = Agent(
    llm=extract_llm,
    goal="Extract the requested information based on a given task and return it.",
    role="Summarizer",
    backstory="You are an expert in extracting information given in a task from a markdown",
    verbose=True,
)

extract_task = Task(
    description="Extract the information requested in the {task} from {markdown}",
    agent=extract_agent,
    expected_output="Requested data",
)

extract_crew = Crew(
    agents=[extract_agent],
    tasks=[extract_task],
    process=Process.sequential,
    max_rpm=1,
    verbose=True,
)

# Main code


async def main():
    global page, elements

    setup()

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(viewport={"width": 1280, "height": 1024})

        page = await context.new_page()
        await page.goto("https://www.destandaard.be")
        await page.wait_for_load_state("networkidle")

        user_task = "Give a quick overview of the 10 latest news articles. No need to search!"
        plan_guide = "Only do a 2 step plan because the info is on the main page."
        
        plan_crew_result = plan_crew.kickoff(inputs={"user_question": user_task, "plan_guide": plan_guide})
        execution_plan = TaskList.model_validate(plan_crew_result.pydantic)
        export_token_use(plan_crew_result.token_usage)

        previous_task = None
        tasks = execution_plan.tasks
        for i, task in enumerate(tasks):
            task = f"{task.Nr} - {task.Task} - {task.Outcome}"

            if i == len(tasks) - 1:
                markdown = await extract_markdown(page, len(tasks) - 1)
                response = extract_crew.kickoff(
                    inputs={"task": task, "markdown": markdown}
                )
                export_token_use(response.token_usage)
            else:
                elements = await extract_elements(page, i)
                minified_elements = prepare_elements(elements, i)

                response = interact_crew.kickoff(
                    inputs={
                        "task": task,
                        "previous": previous_task,
                        "elements": minified_elements,
                    }
                )
                export_token_use(response.token_usage)

            previous_task = task
            input("Press any key to continue")

        input("Click any key to close")
        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
