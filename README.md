以下是根據你的專案結構和需求撰寫的 README.md 文件：

---

# Benchmark

Benchmark's core mission is to provide a robust platform for evaluating AI-generated responses, ensuring high-quality insights and decisions through effective **Capture**, **Organize**, **Distill**, and **Apply** workflows.

## Requirements Extensions

- Python development extensions (e.g., `ms-python.python`, `ms-python.vscode-pylance`, etc.)
- [EditorConfig](https://marketplace.visualstudio.com/items?itemName=EditorConfig.EditorConfig)
- [Ruff](https://marketplace.visualstudio.com/items?itemName=charliermarsh.ruff)

## Recommended Extensions

- [Code Spell Checker](https://marketplace.visualstudio.com/items?itemName=streetsidesoftware.code-spell-checker)
- [Doxygen Documentation Generator](https://marketplace.visualstudio.com/items?itemName=cschlosser.doxdocgen)

## Core Dependencies

- Python 3.12
- Django 5.1

## Getting Started

1. Install [uv](https://docs.astral.sh/uv/getting-started/installation/#installing-uv).

2. Install Python 3.12.

   ```shell
   uv python install 3.12
   ```

3. Create a virtual environment:

   ```shell
   uv venv -p 3.12
   ```

4. Install the dependencies:

   ```shell
   uv sync
   ```

5. Activate the virtual environment.

6. Install the pre-commit hooks:

   ```shell
   pre-commit install
   ```

   To run pre-commit hooks manually:

   ```shell
   pre-commit run --all-files
   ```

## Running Locally

1. Ensure dependencies are installed.
2. Copy .env.example to .env and configure environment variables.
3. Activate the virtual environment.
4. Run the server:

   ```shell
   python manage.py runserver
   ```

   Alternatively, run the asynchronous server with Uvicorn:

   ```shell
   python -m uvicorn config.asgi:application
   ```

## Testing

We use `pytest` and `coverage` for testing. Ensure test coverage remains above 80%.

1. Run tests and generate a coverage report:

   ```shell
   pytest
   ```

2. View the coverage report:

   Open `htmlcov/index.html` in your browser.

If coverage falls **below 80%**, include a detailed explanation justifying the uncovered code areas.

### API Testing with Hoppscotch

1. Open Hoppscotch.
2. Join the shared workspace (contact the team for an invite link).
3. Use the provided API collection for testing.
4. Configure environment variables in Hoppscotch (e.g., `host`, `user_email`, `user_password`).

## Notes

- Every model must inherit `BaseModel` from `common.models`.
- Every admin register class must inherit `BaseAdmin` from `common.admin`.

---

這份 README.md 文件已根據你的專案需求進行了定制，並包含了所有必要的指導步驟和配置說明。