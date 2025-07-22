# PMP Documentation Assistant API - Documentation

**Version:** 1.0.0
**Contact:** [Your Name/Email]

## 1. Overview

The PMP Documentation Assistant is a powerful backend service designed to automate the creation of essential Project Management Professional (PMP) documents. By providing initial project details, the API leverages an advanced AI agentic workflow to generate a comprehensive suite of documents, including a Project Charter, Scope Statement, WBS, and more.

This service is ideal for project managers who want to streamline their documentation process, ensure consistency, and save significant time.

## 2. Core Architecture

The API is built using Python with the **FastAPI** framework. It uses a background task processing model to handle the long-running AI generation process without blocking the user.

-   **API Framework:** FastAPI
-   **Background Jobs:** Native FastAPI `BackgroundTasks`
-   **AI Workflow:** LangGraph
-   **Language Model:** Cohere
-   **Data Storage:** Redis (via Upstash) for storing project state and results.

## 3. API Endpoints

The API exposes three primary endpoints to manage the project lifecycle.

### 3.1. `POST /projects` - Create a New Project

This is the starting point. The frontend sends the initial project data to this endpoint to kick off the generation process.

-   **Method:** `POST`
-   **URL:** `/projects`
-   **Description:** Accepts project parameters and starts the document generation process in the background. The API immediately returns a `project_id` which is used to track the project's progress.
-   **Success Response:** `2022 Accepted`
    -   This status code indicates that the request has been accepted for processing, but the work has not been completed yet.

#### Request Body

The request body must be a JSON object with the following structure.

```json
{
  "project_title": "string (required)",
  "project_description": "string (required)",
  "project_type": "string (required)",
  "key_stakeholders": ["string", "..."],
  "project_objectives": ["string", "..."],
  "project_duration": "string",
  "budget_range": "string",
  "team_size": "string",
  "constraints": "string",
  "assumptions": "string"
}
```

#### Example Response Body

```json
{
  "project_id": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
  "message": "Project generation has been started."
}
```

### 3.2. `GET /projects/{project_id}/status` - Check Project Status

This endpoint allows the frontend to poll the server to check the status of a running project.

-   **Method:** `GET`
-   **URL:** `/projects/{project_id}/status`
-   **Description:** Checks the status of a project generation task using the `project_id` returned from the creation step.
-   **Success Response:** `200 OK`

#### Possible Statuses:

-   `PENDING`: The task has been received but has not started yet.
-   `RUNNING`: The AI workflow is actively generating documents.
-   `COMPLETE`: The workflow has finished successfully.
-   `FAILED`: An error occurred during generation.

#### Example Response Body

```json
{
  "project_id": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
  "status": "COMPLETE",
  "error": null
}
```

### 3.3. `GET /projects/{project_id}/download/{doc_type}` - Download a Document

Once a project's status is `COMPLETE`, the frontend can use this endpoint to download the generated documents.

-   **Method:** `GET`
-   **URL:** `/projects/{project_id}/download/{doc_type}`
-   **Description:** Downloads a specific generated document for a completed project.
-   **Success Response:** `200 OK` with the file content. The response will have the correct `Content-Type` and `Content-Disposition` headers to trigger a file download in the browser.

#### Available `doc_type` values:

-   `charter`
-   `scope`
-   `wbs`
-   `risk-register`
-   `stakeholder-analysis`
-   `communication-plan`

---

## 4. Frontend Integration Guide

This section provides a step-by-step guide for a frontend developer to integrate with the API.

### Step 1: The Project Creation Form

Create a form with fields corresponding to the `POST /projects` request body.

-   **Required Fields:** Project Title, Project Description, Project Type.
-   **Optional Fields:** Key Stakeholders, Objectives, Duration, Budget, etc. These can be simple text inputs or text areas. For lists like `key_stakeholders`, you can use a text input where users enter comma-separated values, which the frontend can then split into a JSON array before sending.

### Step 2: The API Call Workflow

Here is the recommended user flow and corresponding API calls:

1.  **User Submits Form:** When the user fills out the form and clicks "Generate", the frontend should:
    a.  Display a loading indicator (e.g., a spinner).
    b.  Make a `POST` request to the `/projects` endpoint with the form data as a JSON payload.
    c.  On success, store the `project_id` from the response in the frontend's state (e.g., React state, Vuex store).

2.  **Polling for Status:**
    a.  Immediately after receiving the `project_id`, start polling the `/projects/{project_id}/status` endpoint.
    b.  A good polling interval is every 2-3 seconds.
    c.  Use JavaScript's `setInterval()` to make the `GET` request repeatedly.
    d.  Update the UI with the current status (e.g., "Status: RUNNING").

3.  **Handling Completion or Failure:**
    a.  When the status endpoint returns `COMPLETE`:
        i.  Stop the polling (`clearInterval()`).
        ii. Hide the loading indicator.
        iii. Display a "Success!" message and show a list of download links for the available documents.
    b.  When the status endpoint returns `FAILED`:
        i.  Stop the polling.
        ii. Hide the loading indicator.
        iii. Display an error message to the user, including the `error` message from the API response if available.

### Step 3: Creating Download Links

Once the project is `COMPLETE`, generate the download links dynamically. For each available document type, create an `<a>` tag pointing to the download endpoint.

**Example HTML/JSX:**

```html
<!-- Assuming 'projectId' is stored in your component's state -->
<div>
  <h3>Your documents are ready:</h3>
  <ul>
    <li><a href="http://<your_api_url>/projects/${projectId}/download/charter" target="_blank">Download Project Charter</a></li>
    <li><a href="http://<your_api_url>/projects/${projectId}/download/scope" target="_blank">Download Scope Statement</a></li>
    <!-- Add other document links here -->
  </ul>
</div>
```

By setting the `href` directly, the browser will handle the file download automatically based on the response headers from the API.

### Example JavaScript Code Snippet

This pseudo-code illustrates the core logic.

```javascript
// State variables
let projectId = null;
let pollingInterval = null;

// Function to handle form submission
async function handleFormSubmit(formData) {
  try {
    // Show loading spinner
    const response = await fetch('/projects', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(formData),
    });

    if (response.status === 202) {
      const data = await response.json();
      projectId = data.project_id;
      // Start polling for status
      pollingInterval = setInterval(checkStatus, 3000);
    } else {
      // Handle initial submission error
    }
  } catch (error) {
    // Handle network error
  }
}

// Function to poll for status
async function checkStatus() {
  if (!projectId) return;

  try {
    const response = await fetch(`/projects/${projectId}/status`);
    const data = await response.json();

    // Update UI with data.status

    if (data.status === 'COMPLETE' || data.status === 'FAILED') {
      clearInterval(pollingInterval);
      // Hide loading spinner
      if (data.status === 'COMPLETE') {
        // Show download links
      } else {
        // Show error message
      }
    }
  } catch (error) {
    // Handle network error during polling
  }
}
```

---

## 5. Backend Developer Guide

This guide is for developers working on the backend service. It covers project setup, configuration, and how to extend the application with new features.

### 5.1. Local Setup

1.  **Clone the Repository:**
    ```bash
    git clone <your_repository_url>
    cd <project_folder>
    ```

2.  **Create a Python Virtual Environment:**
    It's crucial to use a virtual environment to manage dependencies.
    ```bash
    # For Windows
    python -m venv .venv
    .\.venv\Scripts\activate

    # For macOS/Linux
    python3 -m venv .venv
    source .venv/bin/activate
    ```

3.  **Install Dependencies:**
    All required packages are listed in `requirements.txt`.
    ```bash
    pip install -r requirements.txt
    ```

### 5.2. Configuration

The application is configured using environment variables stored in a `.env` file in the project root.

1.  Create a file named `.env`.
2.  Add the following required variables:

    ```env
    # Get this from your Upstash Redis database dashboard
    UPSTASH_REDIS_URL="rediss://:your_password@your_hostname:your_port"

    # Get this from your Cohere dashboard
    COHERE_API_KEY="your_cohere_api_key"
    ```

### 5.3. Running the Application

With the virtual environment activated and the `.env` file configured, run the FastAPI server using Uvicorn:

```bash
uvicorn pmp_project.main:app --reload
```

The API will be available at `http://127.0.0.1:8000`, and the interactive documentation can be found at `http://127.0.0.1:8000/docs`.

### 5.4. Project Structure Overview

-   `pmp_project/main.py`: The main FastAPI application file. Defines API endpoints and background task logic.
-   `pmp_project/graph.py`: Defines the LangGraph workflow, connecting all the generation nodes in the correct sequence.
-   `pmp_project/state.py`: Contains all Pydantic models for API input (`ProjectInput`) and data structures for the graph state (`GraphState`, `CharterOutput`, etc.).
-   `pmp_project/nodes/`: This directory contains the core logic. Each file represents a node in the graph that performs a specific task (e.g., `generation_nodes.py` calls the LLM).
-   `pmp_project/redis_client.py`: Handles the connection to the Redis database.
-   `pmp_project/docx_generator.py`: Contains functions to generate `.docx` files from the final JSON data.

### 5.5. How to Add a New Document Type

Let's say you want to add a "Project Budget" document.

1.  **Update `DocumentType` Enum:** In `pmp_project/main.py`, add `"budget"` to the `DocumentType` enum.

2.  **Create Pydantic Output Model:** In `pmp_project/state.py`, define a new Pydantic model for the budget's structure (e.g., `BudgetOutput`).

3.  **Create Generation Node:** In a relevant file in the `nodes/` directory (or a new one like `nodes/financial_nodes.py`), create a new function `generate_budget_node(state: GraphState)`. This function will contain the prompt and LLM call to generate the budget data.

4.  **Add Node to Graph:** In `pmp_project/graph.py`, import your new node and add it to the graph using `workflow.add_node()`. Then, add an edge to connect it to the workflow, for example, after the `charter` is generated.

5.  **Create DOCX Generator:** In `pmp_project/docx_generator.py`, create a new function `generate_budget_docx(data, project_name)` that takes the generated budget data and creates a `.docx` file.

6.  **Map in `main.py`:** In `pmp_project/main.py`, add the new document type and its generator function to the `DOC_GENERATOR_MAP` dictionary.

This modular structure makes the application highly extensible.