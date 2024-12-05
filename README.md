# 🌱 AI Web Scraper experiment

Welcome to the **Web Scraper Experiment**! 🌟 This project is a playful exploration into using Large Language Models (LLMs) and an agentic approach to interact with webpages and extract data. With this approach it's possible to describe what should be done and based on that the steps on the webpage are executed and data is extracted. 
No need to write css selectors or anything else.

The current setting is to use 2 different models:
- groq/llama-3.2-90b-vision-preview
- gemini/gemini-1.5-flash

## 🧪 How It Works

You start by defining the URL you want to extract data from and providing a `user_task` along with an optional `plan_guide`. Based on these inputs, a plan is generated to extract the necessary data. This planning is orchestrated by the **planning agent**, which utilizes the `gemini-1.5-flash` LLM to create a step-by-step task list tailored to achieve the specified goal. The agents then autonomously navigate the website, interact with elements, and extract the required information, converting it into Markdown format without the need for manual intervention or detailed code adjustments.

It is also capable of doing multiple interactions, for example accepting cookie consent, searching, ...

## 🖼️ Some in program screenshots
Build up planning + intial step
![Planning](./content/Screenshot%202024-12-05%20at%2015.51.01.png)

Content extraction
![Content Extraction](./content/Screenshot%202024-12-05%20at%2015.51.16.png)

### Interaction Process

For interactions, two agents are involved, combining the capabilities of `gemini-1.5-flash` and `groq/llama-3.2-90b-vision-preview`:

1. **Scraping and Preparing Elements**:
   - **HTML Extraction**: The agents first scrape the HTML elements within the viewport.
   - **Sanitization & Minification**: The scraped elements are then sanitized and minified to ensure clean and efficient data processing.
   
2. **Element Interaction**:
   - **Page Scrape Agent**: This agent analyzes the task at hand and determines which element to interact with. It returns the ID of the target element and, if applicable, a string to be entered into an `input` element.
   - **Page Execute Agent**: Using the data provided by the Page Scrape Agent, this agent prepares the necessary arguments for the `interact_with_element` tool, which executes the corresponding Playwright command to interact with the webpage element.

### Why Use Different Models?

You might wonder why multiple models are used. Here are the key reasons:

- **Cost Efficiency**: The models used (`gemini-1.5-flash` and `groq/llama-3.2-90b-vision-preview`) are available for free and are rate-limited. By utilizing multiple models, the system can operate within these rate limits without incurring costs.
- **Task Optimization**: Different models can be allocated to tasks based on their complexity. Less capable (and cheaper) models can handle simpler tasks, while more advanced models manage complex interactions, optimizing resource usage.

### Steering Output and Plans

The output and execution plan can be tailored by adjusting the `user_task` and `plan_guide`. This flexibility allows you to guide the agents to focus on specific aspects of data extraction and interaction, enabling more precise and relevant results based on your requirements.

## 🔮 Future
Well here the option could be the actually leverage the vision capabilities, because currently it's fully working on extracted HTML elements. The experiment currently contains code to dump a screenshot & create bounding boxes around interactive elements. 

Perhaps I'll give it a try and see what the impact is on token consumption ....

## 🛠️ Tools & frameworks used
- [CrewAI](https://docs.crewai.com/introduction) - To build the agent setup and experiment
- [Groq](https://console.groq.com/playground) - Groq models
- [Gemini](https://gemini.google.com/app) - Google Gemini models

## 📦 Getting Started

### 🛠️ Prerequisites

Before diving into the experiment, ensure you have the following installed:

- **Python 3.8+**: A versatile programming language essential for running the scripts.

### 📥 Clone the Repository

Begin by cloning this experimental repository to your local machine. This will set up the necessary files and structure for you to start exploring.

### 🐍 Set Up the Environment

It's recommended to use a virtual environment to manage dependencies and maintain a clean workspace. This ensures that all necessary packages are isolated and do not interfere with other projects.

Install the necessary Python packages to enable the functionalities of LLMs and agentic scraping.

Additionally, set up Playwright browsers to allow the automation scripts to interact with web pages seamlessly.

## ⚙️ Configuration

Create a `.env.local` file in the root directory to set up your environment variables. This file will hold configurations that tailor the experiment to your specific needs.

### Example `.env.local`

Set the following 2 variables
```env
GROQ_API_KEY=<YOUR KEY>
GEMINI_API_KEY=<YOUR KEY>
```

### Install dependencies
```bash
pip install -r requirements.txt
```

### Running the application

Adapt the url + `user_task` + `plan_guide` in `main.py` and run:

```bash
python ./main.py
```