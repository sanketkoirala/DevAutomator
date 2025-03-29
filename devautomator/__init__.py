#!/usr/bin/env python3
import os
import subprocess
import click
import shutil

def ensure_directory(directory: str) -> None:
    """Ensure that a directory exists, creating it if necessary."""
    if not os.path.exists(directory):
        os.makedirs(directory)
        click.echo(f"Created directory '{directory}'.")
    else:
        click.echo(f"Directory '{directory}' already exists.")

def run_command(command: list, cwd: str = None, check: bool = True) -> None:
    try:
        result = subprocess.run(
            command, cwd=cwd, capture_output=True, text=True, check=check
        )
        if result.stdout:
            click.echo(result.stdout)
        if result.stderr:
            click.echo(result.stderr)
    except subprocess.CalledProcessError as e:
        click.echo(f"Command '{' '.join(command)}' failed with error:\n{e.stderr}")
    except FileNotFoundError:
        click.echo(f"Command '{command[0]}' not found. Please ensure it is installed.")

def get_test_metrics(path="."):
    """Run pytest in collect-only mode and return the total number of tests collected."""
    try:
        result = subprocess.run(["pytest", "--collect-only", path], capture_output=True, text=True)
        output = result.stdout.strip()
        collected = None
        for line in output.splitlines():
            if "collected" in line:
                parts = line.split()
                for i, part in enumerate(parts):
                    if part == "collected" and i + 1 < len(parts):
                        try:
                            collected = int(parts[i + 1])
                            break
                        except ValueError:
                            continue
        return collected if collected is not None else "Unknown"
    except Exception as e:
        return f"Error: {e}"

def get_git_metrics():
    """If in a Git repo, return the current branch and count of uncommitted changes."""
    if not os.path.exists(".git"):
        return None, None
    try:
        branch_result = subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"],
                                       capture_output=True, text=True)
        branch = branch_result.stdout.strip()
        status_result = subprocess.run(["git", "status", "--porcelain"],
                                       capture_output=True, text=True)
        changes = status_result.stdout.strip().splitlines()
        changes_count = len(changes)
        return branch, changes_count
    except Exception:
        return None, None

def get_doc_status(project_path="."):
    """Check if documentation is set up (i.e. docs folder with conf.py exists)."""
    docs_dir = os.path.join(project_path, 'docs')
    if os.path.exists(docs_dir):
        conf_file = os.path.join(docs_dir, 'conf.py')
        if os.path.exists(conf_file):
            return "Documentation is set up."
        else:
            return "Docs folder exists but 'conf.py' is missing."
    else:
        return "Documentation not set up."

def cleanup_project(path="."):
    """
    Recursively remove common temporary files and directories:
      - Directories: __pycache__, .pytest_cache, .mypy_cache
      - Files: *.pyc, *.pyo
    Returns a tuple of (removed_directories, removed_files).
    """
    removed_dirs = []
    removed_files = []
    for root, dirs, files in os.walk(path):
        # Remove unwanted directories
        for d in list(dirs):
            if d in ("__pycache__", ".pytest_cache", ".mypy_cache"):
                full_dir = os.path.join(root, d)
                try:
                    shutil.rmtree(full_dir)
                    removed_dirs.append(full_dir)
                    dirs.remove(d) 
                except Exception as e:
                    click.echo(f"Error removing directory {full_dir}: {e}")
        # Remove unwanted files
        for file in files:
            if file.endswith(".pyc") or file.endswith(".pyo"):
                full_file = os.path.join(root, file)
                try:
                    os.remove(full_file)
                    removed_files.append(full_file)
                except Exception as e:
                    click.echo(f"Error removing file {full_file}: {e}")
    return removed_dirs, removed_files

@click.group(context_settings={'help_option_names': ['-h', '--help']})
def cli():
    """DevAutomator: Your Personal Dev Automation Assistant

Commands: \n
  tf         Initialize a Terraform project with standard TF files \n
  docker     Scaffold a Docker configuration \n
  env        Create a Python virtual environment \n
  test       Run pytest on the tests/ directory \n
  doc        Set up documentation for the project \n
  dep        Check for outdated dependencies \n
  scaffold   Scaffold a new project interactively \n
  mkdoc      Generate a Markdown documentation (README) of the project structure \n
  cleanup    Clean up temporary files and directories \n
  dashboard  Display real-time project metrics \n
  helpinfo   Show detailed help for all commands \n

Examples: \n                                                          
  devautomator tf my_project       # Initialize a Terraform project \n
  devautomator docker my_project   # Scaffold a Docker configuration \n
  devautomator env myenv           # Create a Python virtual environment \n
  devautomator test tests/         # Run pytest on the tests/ directory \n
  devautomator doc my_project      # Set up documentation for the project \n
  devautomator dep my_project      # Check for outdated dependencies \n
  devautomator scaffold my_project  # Scaffold a new project interactively \n
  devautomator mkdoc               # Generate project documentation as a Markdown file \n
  devautomator cleanup             # Clean up temporary files and directories \n
  devautomator dashboard .         # Display real-time project metrics \n
  devautomator helpinfo            # Show detailed help for all commands \n

For detailed help on any command, run: \n
  devautomator COMMAND --help
"""
    pass

@cli.command()
@click.argument('project_name')
def tf(project_name):
    """
    Initialize a Terraform project by creating a directory and standard Terraform configuration files:
      - main.tf
      - variables.tf
      - outputs.tf
      - locals.tf
    Then run 'terraform init'.

    Example:
      devautomator tf my_project
    """
    ensure_directory(project_name)
    main_tf = os.path.join(project_name, "main.tf")
    variables_tf = os.path.join(project_name, "variables.tf")
    outputs_tf = os.path.join(project_name, "outputs.tf")
    locals_tf = os.path.join(project_name, "locals.tf")
    with open(main_tf, 'w') as f:
        f.write(
            'terraform {\n'
            '  required_version = ">= 0.12"\n'
            '  backend "local" {\n'
            '    path = "terraform.tfstate"\n'
            '  }\n'
            '}\n\n'
            'provider "aws" {\n'
            '  region = var.region\n'
            '}\n'
        )
    click.echo("Created main.tf with standard Terraform configuration.")
    with open(variables_tf, 'w') as f:
        f.write(
            '// Variable definitions\n'
            'variable "region" {\n'
            '  description = "The AWS region"\n'
            '  type        = string\n'
            '  default     = "us-east-1"\n'
            '}\n'
        )
    click.echo("Created variables.tf with variable definitions.")
    with open(outputs_tf, 'w') as f:
        f.write(
            '// Output definitions\n'
            'output "example_output" {\n'
            '  description = "An example output"\n'
            '  value       = "Hello, Terraform!"\n'
            '}\n'
        )
    click.echo("Created outputs.tf with output definitions.")
    with open(locals_tf, 'w') as f:
        f.write(
            '// Local values\n'
            'locals {\n'
            '  example_local = "This is a local value"\n'
            '}\n'
        )
    click.echo("Created locals.tf with local value definitions.")
    run_command(["terraform", "init"], cwd=project_name)

@cli.command()
@click.argument('project_name')
def docker(project_name):
    """
    Scaffold Docker configuration: creates a Dockerfile and docker-compose.yml.

    Example:
      devautomator docker my_docker_project
    """
    ensure_directory(project_name)
    dockerfile_path = os.path.join(project_name, 'Dockerfile')
    with open(dockerfile_path, 'w') as f:
        f.write(
            "FROM python:3.9-slim\n"
            "WORKDIR /app\n"
            "COPY . /app\n"
            "RUN pip install -r requirements.txt\n"
            "CMD [\"python\", \"app.py\"]\n"
        )
    click.echo("Created Dockerfile.")
    compose_path = os.path.join(project_name, 'docker-compose.yml')
    with open(compose_path, 'w') as f:
        f.write(
            "version: '3'\n"
            "services:\n"
            "  app:\n"
            "    build: .\n"
            "    ports:\n"
            "      - \"5000:5000\"\n"
        )
    click.echo("Created docker-compose.yml.")

@cli.command()
@click.argument('env_name')
def env(env_name):
    """
    Create a new Python virtual environment.

    Example:
      devautomator env myenv
    """
    run_command(["python", "-m", "venv", env_name])

@cli.command()
@click.argument('path', default='.')
def test(path):
    """
    Run tests using pytest on the specified path.

    Example:
      devautomator test path/to/tests
    """
    click.echo(f"Running tests in '{path}'...")
    run_command(["pytest", path])

@cli.command()
@click.argument('project_name')
def doc(project_name):
    """
    Generate basic documentation setup for a project using Sphinx.

    Example:
      devautomator doc my_project
    """
    docs_dir = os.path.join(project_name, 'docs')
    ensure_directory(docs_dir)
    sphinx_conf = os.path.join(docs_dir, 'conf.py')
    with open(sphinx_conf, 'w') as f:
        f.write("# Sphinx configuration\n")
    click.echo("Created Sphinx configuration file 'conf.py'.")
    click.echo("You can now build your docs using 'sphinx-build'.")

@cli.command()
@click.argument('project_name')
def dep(project_name):
    """
    Check for outdated Python dependencies for a project.

    Example:
      devautomator dep my_project
    """
    click.echo(f"Checking outdated dependencies for project '{project_name}'...")
    run_command(["pip", "list", "--outdated"])

@cli.command()
@click.argument('project_name')
def scaffold(project_name):
    """
    Scaffold a new project with boilerplate code interactively.
    
    This command will prompt you for the type of project:
      - cli      : Creates a CLI project with a main file, tests directory, README, requirements.txt, and setup.py.
      - web      : For web projects, you'll be asked if it is a frontend or backend app.
                   For a frontend app, you can choose React or Angular.
                   For a backend app, you can choose from express, nestjs, fastapi, flask, spring, or tote.
      - generic  : Creates a basic project structure with README and requirements.txt.
    
    Example:
      devautomator scaffold my_project
    """
    ensure_directory(project_name)
    click.echo(f"Scaffolding project '{project_name}'...")
    project_type = click.prompt("What type of project is this?", 
                                type=click.Choice(['cli', 'web', 'generic'], case_sensitive=False))
    if project_type.lower() == "cli":
        main_file = os.path.join(project_name, 'main.py')
        with open(main_file, 'w') as f:
            f.write(
                "import click\n\n"
                "@click.command()\n"
                "def main():\n"
                "    click.echo('Hello from your CLI tool!')\n\n"
                "if __name__ == '__main__':\n"
                "    main()\n"
            )
        tests_dir = os.path.join(project_name, 'tests')
        ensure_directory(tests_dir)
        test_file = os.path.join(tests_dir, 'test_main.py')
        with open(test_file, 'w') as f:
            f.write(
                "from main import main\n\n"
                "def test_main(capsys):\n"
                "    main()\n"
                "    captured = capsys.readouterr()\n"
                "    assert 'Hello from your CLI tool!' in captured.out\n"
            )
        with open(os.path.join(project_name, 'README.md'), 'w') as f:
            f.write(f"# {project_name}\n\nA CLI project scaffolded with DevAutomator.\n")
        with open(os.path.join(project_name, 'requirements.txt'), 'w') as f:
            f.write("click\n")
        with open(os.path.join(project_name, 'setup.py'), 'w') as f:
            f.write(
                "from setuptools import setup\n\n"
                "setup(\n"
                f"    name='{project_name}',\n"
                "    version='0.1.0',\n"
                "    py_modules=['main'],\n"
                "    install_requires=['click'],\n"
                "    entry_points={'console_scripts': [\n"
                f"        '{project_name}=main:main'\n"
                "    ]},\n"
                ")\n"
            )
        click.echo("CLI project scaffolded successfully.")
    elif project_type.lower() == "web":
        app_type = click.prompt("Is your web project a frontend or backend app?",
                                type=click.Choice(['frontend', 'backend'], case_sensitive=False))
        if app_type.lower() == "frontend":
            framework = click.prompt("Which frontend framework do you want? (react/angular)",
                                     type=click.Choice(['react', 'angular'], case_sensitive=False))
            if framework.lower() == "react":
                ensure_directory(os.path.join(project_name, "public"))
                ensure_directory(os.path.join(project_name, "src"))
                with open(os.path.join(project_name, "public", "index.html"), 'w') as f:
                    f.write(
                        "<!DOCTYPE html>\n"
                        "<html lang='en'>\n"
                        "<head>\n"
                        "  <meta charset='UTF-8'>\n"
                        "  <meta name='viewport' content='width=device-width, initial-scale=1.0'>\n"
                        "  <title>React App</title>\n"
                        "</head>\n"
                        "<body>\n"
                        "  <div id='root'></div>\n"
                        "  <script src='../src/index.js'></script>\n"
                        "</body>\n"
                        "</html>\n"
                    )
                with open(os.path.join(project_name, "src", "index.js"), 'w') as f:
                    f.write(
                        "import React from 'react';\n"
                        "import ReactDOM from 'react-dom';\n\n"
                        "const App = () => <h1>Welcome to your React App!</h1>;\n\n"
                        "ReactDOM.render(<App />, document.getElementById('root'));\n"
                    )
                with open(os.path.join(project_name, "package.json"), 'w') as f:
                    f.write(
                        "{\n"
                        f'  "name": "{project_name}",\n'
                        '  "version": "0.1.0",\n'
                        '  "dependencies": {\n'
                        '    "react": "^17.0.0",\n'
                        '    "react-dom": "^17.0.0"\n'
                        "  },\n"
                        '  "scripts": {\n'
                        '    "start": "echo \\"Run your bundler here\\""\n'
                        "  }\n"
                        "}\n"
                    )
                click.echo("React frontend project scaffolded successfully.")
            elif framework.lower() == "angular":
                ensure_directory(os.path.join(project_name, "src"))
                with open(os.path.join(project_name, "src", "app.component.ts"), 'w') as f:
                    f.write(
                        "import { Component } from '@angular/core';\n\n"
                        "@Component({\n"
                        "  selector: 'app-root',\n"
                        "  template: `<h1>Welcome to your Angular App!</h1>`\n"
                        "})\n"
                        "export class AppComponent {}\n"
                    )
                with open(os.path.join(project_name, "package.json"), 'w') as f:
                    f.write(
                        "{\n"
                        f'  "name": "{project_name}",\n'
                        '  "version": "0.1.0",\n'
                        '  "dependencies": {\n'
                        '    "@angular/core": "~12.0.0"\n'
                        "  },\n"
                        '  "scripts": {\n'
                        '    "start": "echo \\"Run Angular CLI to serve your app\\""\n'
                        "  }\n"
                        "}\n"
                    )
                click.echo("Angular frontend project scaffolded successfully.")
        elif app_type.lower() == "backend":
            backend_framework = click.prompt("Which backend framework do you want? (express, nestjs, fastapi, flask, spring, tote)",
                                             type=click.Choice(['express', 'nestjs', 'fastapi', 'flask', 'spring', 'tote'], case_sensitive=False))
            if backend_framework.lower() == "express":
                with open(os.path.join(project_name, "index.js"), 'w') as f:
                    f.write(
                        "const express = require('express');\n"
                        "const app = express();\n"
                        "const PORT = process.env.PORT || 3000;\n\n"
                        "app.get('/', (req, res) => res.send('Hello from Express!'));\n\n"
                        "app.listen(PORT, () => console.log(`Server running on port ${PORT}`));\n"
                    )
                with open(os.path.join(project_name, "package.json"), 'w') as f:
                    f.write(
                        "{\n"
                        f'  "name": "{project_name}",\n'
                        '  "version": "0.1.0",\n'
                        '  "dependencies": {\n'
                        '    "express": "^4.17.1"\n'
                        "  },\n"
                        '  "scripts": {\n'
                        '    "start": "node index.js"\n'
                        "  }\n"
                        "}\n"
                    )
                click.echo("Express backend project scaffolded successfully.")
            elif backend_framework.lower() == "nestjs":
                with open(os.path.join(project_name, "main.ts"), 'w') as f:
                    f.write(
                        "import { NestFactory } from '@nestjs/core';\n"
                        "import { AppModule } from './app.module';\n\n"
                        "async function bootstrap() {\n"
                        "  const app = await NestFactory.create(AppModule);\n"
                        "  await app.listen(3000);\n"
                        "}\n"
                        "bootstrap();\n"
                    )
                with open(os.path.join(project_name, "app.module.ts"), 'w') as f:
                    f.write(
                        "import { Module } from '@nestjs/common';\n\n"
                        "@Module({\n"
                        "  imports: [],\n"
                        "  controllers: [],\n"
                        "  providers: [],\n"
                        "})\n"
                        "export class AppModule {}\n"
                    )
                click.echo("NestJS backend project scaffolded successfully.")
            elif backend_framework.lower() == "fastapi":
                with open(os.path.join(project_name, "main.py"), 'w') as f:
                    f.write(
                        "from fastapi import FastAPI\n\n"
                        "app = FastAPI()\n\n"
                        "@app.get('/')\n"
                        "def read_root():\n"
                        "    return {'message': 'Hello from FastAPI!'}\n"
                    )
                with open(os.path.join(project_name, "requirements.txt"), 'w') as f:
                    f.write("fastapi\nuvicorn\n")
                click.echo("FastAPI backend project scaffolded successfully.")
            elif backend_framework.lower() == "flask":
                with open(os.path.join(project_name, "app.py"), 'w') as f:
                    f.write(
                        "from flask import Flask\n\n"
                        "app = Flask(__name__)\n\n"
                        "@app.route('/')\n"
                        "def hello():\n"
                        "    return 'Hello from Flask!'\n\n"
                        "if __name__ == '__main__':\n"
                        "    app.run(debug=True)\n"
                    )
                with open(os.path.join(project_name, "requirements.txt"), 'w') as f:
                    f.write("flask\n")
                click.echo("Flask backend project scaffolded successfully.")
            elif backend_framework.lower() == "spring":
                with open(os.path.join(project_name, "README.md"), 'w') as f:
                    f.write(f"# {project_name}\n\nThis is a Spring backend project. Please use Spring Initializr or your IDE to generate a full project.\n")
                click.echo("Spring backend project scaffolded (README only).")
            elif backend_framework.lower() == "tote":
                with open(os.path.join(project_name, "README.md"), 'w') as f:
                    f.write(f"# {project_name}\n\nThis backend project uses a custom 'tote' framework. Customize as needed.\n")
                click.echo("Tote backend project scaffolded (README only).")
        click.echo("Web project scaffolded successfully.")
    else:
        with open(os.path.join(project_name, 'README.md'), 'w') as f:
            f.write(f"# {project_name}\n\nA new {project_type} project scaffolded with DevAutomator.\n")
        with open(os.path.join(project_name, 'requirements.txt'), 'w') as f:
            f.write("")
        click.echo("Generic project scaffolded successfully.")
    click.echo("Project scaffolded successfully.")

@cli.command()
def mkdoc():
    """
    Generate a Markdown documentation file (README_generated.md) for the current project
    by scanning all folders and files in the current directory.

    Example:
      devautomator mkdoc
    """
    output_file = "README_generated.md"
    tree_lines = ["# Project Documentation", "", "## Directory Structure", ""]
    for root, dirs, files in os.walk("."):
        # Skip hidden directories/files like .git
        if any(part.startswith('.') for part in root.split(os.sep)):
            continue
        rel_path = os.path.relpath(root, ".")
        tree_lines.append(f"### {rel_path}")
        # List directories
        for d in sorted(dirs):
            tree_lines.append(f"- **Directory:** {d}")
        # List files
        for f in sorted(files):
            tree_lines.append(f"- File: {f}")
        tree_lines.append("") 
    content = "\n".join(tree_lines)
    with open(output_file, "w") as f:
        f.write(content)
    click.echo(f"Documentation generated and saved to {output_file}.")

@cli.command()
def cleanup():
    """
    Clean up temporary files and directories from the project directory.
    This command recursively removes common unwanted directories (e.g. __pycache__,
    .pytest_cache, .mypy_cache) and temporary files (*.pyc, *.pyo).

    Example:
      devautomator cleanup
    """
    target_path = "."
    click.echo(f"Cleaning up temporary files in '{target_path}'...")
    removed_dirs, removed_files = cleanup_project(target_path)
    if removed_dirs:
        click.echo("Removed directories:")
        for d in removed_dirs:
            click.echo(f"  - {d}")
    else:
        click.echo("No temporary directories found to remove.")
    if removed_files:
        click.echo("Removed files:")
        for f in removed_files:
            click.echo(f"  - {f}")
    else:
        click.echo("No temporary files found to remove.")
    click.echo("Cleanup complete.")

@cli.command()
@click.argument('project_path', required=False, default=".")
def dashboard(project_path):
    """
    Display a developer dashboard with real metrics.

    It shows:
      - Total tests collected (using pytest)
      - Git repository details (current branch and uncommitted changes)
      - Documentation status

    Example:
      devautomator dashboard .
    """
    click.echo("Developer Dashboard:")
    test_count = get_test_metrics(project_path)
    click.echo(f"- Total Tests Collected: {test_count}")
    branch, changes_count = get_git_metrics()
    if branch is not None:
        click.echo(f"- Git Branch: {branch}")
        click.echo(f"- Uncommitted Changes: {changes_count}")
    else:
        click.echo("- Git Repository: Not detected")
    doc_status = get_doc_status(project_path)
    click.echo(f"- Documentation: {doc_status}")

@cli.command(name="helpinfo")
def helpinfo():
    """
    Show detailed help for all commands with usage examples.

    Example:
      devautomator helpinfo
    """
    help_text = """
DevAutomator - Developer Automation Tool
------------------------------------------
Usage:
  devautomator [OPTIONS] COMMAND [ARGS]...

Commands and Examples:
  tf         Initialize a Terraform project with standard TF files.
             Example: devautomator tf my_project

  docker     Scaffold a Docker configuration.
             Example: devautomator docker my_project

  env        Create a Python virtual environment.
             Example: devautomator env myenv

  test       Run tests using pytest.
             Example: devautomator test path/to/tests

  doc        Set up documentation using Sphinx.
             Example: devautomator doc my_project

  dep        Check for outdated Python dependencies.
             Example: devautomator dep my_project

  scaffold   Scaffold a new project with boilerplate code.
             Example: devautomator scaffold my_project

  mkdoc      Generate project documentation as a Markdown file.
             Example: devautomator mkdoc

  cleanup    Clean up temporary files and directories.
             Example: devautomator cleanup

  dashboard  Display real-time project metrics.
             Example: devautomator dashboard [project_directory]

For detailed help on any command, run:
  devautomator COMMAND --help
"""
    click.echo(help_text)

if __name__ == '__main__':
    cli()
