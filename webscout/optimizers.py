"""Prompt optimization utilities."""

import os
import platform
import subprocess
from typing import  Literal, Optional,  Tuple, Callable, Dict, Any
class Optimizers:
    """
    >>> Optimizers.code("write a hello world")
    Returns optimized prompt for code generation
    
    >>> Optimizers.shell_command("list files")
    Returns optimized prompt for shell commands
    
    >>> Optimizers.search("best pizza places")
    Returns optimized prompt for web search
    
    >>> Optimizers.math("solve quadratic equation")
    Returns optimized prompt for math problems
    """
    @staticmethod
    def code(prompt: str) -> str:
        """Deprecated: Use coder() instead"""
        return Optimizers.coder(prompt)

    @staticmethod
    def shell_command(prompt: str) -> str:
         """Deprecated: Use coder() instead"""
         return Optimizers.coder(f"!{prompt}")

    @staticmethod
    def coder(prompt: str) -> str:
        """Unified optimizer for both code and shell commands."""
        # Get system info for shell commands
        operating_system: str = ""
        if platform.system() == "Windows":
            operating_system = "Windows"
        elif platform.system() == "Darwin":
            operating_system = "MacOS"
        elif platform.system() == "Linux":
            try:
                result: str = subprocess.check_output(["lsb_release", "-si"]).decode().strip()
                operating_system = f"Linux/{result}" if result else "Linux"
            except Exception:
                operating_system = "Linux"
        else:
            operating_system = platform.system()

        # Get shell info
        shell_name: str = "/bin/sh"
        if platform.system() == "Windows":
            shell_name = "powershell.exe" if os.getenv("PSModulePath") else "cmd.exe"
        else:
            shell_env: Optional[str] = os.getenv("SHELL")
            if shell_env:
                shell_name = shell_env

        return (
            f"""<system_context>
        <role>
          Your Role: You are a code generation expert. Analyze the request and provide appropriate output.
          If the request starts with '!' or involves system/shell operations, provide a shell command.
          Otherwise, provide Python code.
        </role>
        <rules>
           RULES:
             - Provide ONLY code/command output without any description or markdown
             - For shell commands:
                 - Target OS: {operating_system}
                 - Shell: {shell_name}
                 - Combine multiple steps when possible
             - For Python code:
                - Include necessary imports
                - Handle errors appropriately
                - Follow PEP 8 style
             - If details are missing, use most logical implementation
             - No warnings, descriptions, or explanations
        </rules>
        <request>
             Request: {prompt}
        </request>
        <output>
            Output:
        </output>
</system_context>"""
        )

    @staticmethod
    def search(prompt: str) -> str:
         """Optimize prompt for web search queries."""
         return f"""
<system_context>
  <role>
    Your role: Generate a precise and focused web search query.
  </role>
  <instructions>
    IMPORTANT: Return only the search query without any explanation.
    Format: Plain text, no markdown.
    If details are missing, focus on the most relevant aspects.
  </instructions>
 <request>
    Request: {prompt}
 </request>
 <output>
    Search Query:
 </output>
 </system_context>
        """

    @staticmethod
    def math(prompt: str) -> str:
        """Optimize prompt for mathematical problem solving."""
        return f"""
<system_context>
  <role>
     Your role: Solve mathematical problems step by step.
  </role>
  <instructions>
    Format: Plain text, show calculations clearly.
    Show all steps and intermediate results.
    Include units where applicable.
    Provide final answer in a clear format.
  </instructions>
 <request>
     Problem: {prompt}
  </request>
 <output>
     Solution:
  </output>
 </system_context>
        """

    @staticmethod
    def explain(prompt: str) -> str:
        """Optimize prompt for clear explanations."""
        return f"""
<system_context>
  <role>
     Your role: Explain concepts clearly and concisely.
  </role>
  <instructions>
    Format: Break down complex ideas into simple terms.
    Use analogies where helpful.
    Focus on key points and practical understanding.
  </instructions>
   <topic>
     Topic: {prompt}
    </topic>
  <output>
    Explanation:
 </output>
</system_context>
        """

    @staticmethod
    def debug(prompt: str) -> str:
         """Optimize prompt for debugging code."""
         return f"""
<system_context>
  <role>
     Your role: Debug code and identify issues.
  </role>
  <instructions>
    Steps:
     - Identify syntax errors
     - Check logic issues
     - Look for common pitfalls
     - Suggest fixes
  </instructions>
  <input>
     Code to debug: {prompt}
  </input>
 <output>
   Analysis:
 </output>
</system_context>
        """

    @staticmethod
    def api(prompt: str) -> str:
        """Optimize prompt for API endpoint design."""
        return f"""
<system_context>
  <role>
   Your role: Design RESTful API endpoints.
  </role>
  <instructions>
     Include:
      - HTTP methods
      - URL structure
      - Request/Response format
      - Status codes
   </instructions>
    <input>
        API requirement: {prompt}
    </input>
    <output>
        Design:
    </output>
</system_context>
        """

    @staticmethod
    def sql(prompt: str) -> str:
         """Optimize prompt for SQL query generation."""
         return f"""
<system_context>
   <role>
      Your role: Generate optimized SQL queries.
   </role>
   <instructions>
        Requirements:
        - Standard SQL syntax
        - Efficient query structure
        - Proper joins and indexing
        - Consider performance
    </instructions>
    <input>
        Query need: {prompt}
    </input>
  <output>
        SQL:
   </output>
</system_context>
        """

    @staticmethod
    def regex(prompt: str) -> str:
        """Optimize prompt for regex pattern generation."""
        return f"""
<system_context>
    <role>
     Your role: Generate precise regex patterns.
    </role>
   <instructions>
        Requirements:
        - Standard regex syntax
        - Pattern explanation
        - Test cases
        - Consider edge cases
    </instructions>
    <input>
        Pattern need: {prompt}
    </input>
   <output>
         Regex:
     </output>
</system_context>
        """

    @staticmethod
    def test(prompt: str) -> str:
        """Optimize prompt for test case generation."""
        return f"""
<system_context>
  <role>
     Your role: Generate comprehensive test cases.
  </role>
   <instructions>
        Include:
        - Edge cases
        - Corner cases
        - Error scenarios
        - Happy path
        Format: Test name and expected result
   </instructions>
   <input>
      Test requirement: {prompt}
    </input>
    <output>
      Test Cases:
   </output>
</system_context>
        """

    @staticmethod
    def docker(prompt: str) -> str:
        """Optimize prompt for Dockerfile creation."""
        return f"""
<system_context>
  <role>
     Your role: Create efficient Dockerfile.
  </role>
    <instructions>
        Consider:
        - Base image selection
        - Layer optimization
        - Security best practices
        - Multi-stage builds if needed
    </instructions>
    <input>
      Container requirement: {prompt}
    </input>
   <output>
      Dockerfile:
   </output>
</system_context>
        """

    @staticmethod
    def git(prompt: str) -> str:
        """Optimize prompt for git commands."""
        return f"""
<system_context>
   <role>
    Your role: Generate git commands.
  </role>
   <instructions>
        Requirements:
        - Clear and safe commands
        - Consider current state
        - Include safety checks
        - Best practices
    </instructions>
    <input>
     Git task: {prompt}
    </input>
   <output>
    Command:
   </output>
</system_context>
        """

    @staticmethod
    def yaml(prompt: str) -> str:
        """Optimize prompt for YAML configuration."""
        return f"""
<system_context>
    <role>
     Your role: Generate YAML configuration.
    </role>
   <instructions>
        Requirements:
        - Valid YAML syntax
        - Clear structure
        - Comments for complex parts
        - Best practices
   </instructions>
   <input>
     Config need: {prompt}
    </input>
  <output>
    YAML:
  </output>
</system_context>
        """

    @staticmethod
    def cli(prompt: str) -> str:
        """Optimize prompt for CLI command design."""
        return f"""
<system_context>
    <role>
         Your role: Design CLI commands.
    </role>
   <instructions>
        Include:
          - Command structure
          - Arguments/options
          - Help messages
          - Examples
    </instructions>
  <input>
     CLI requirement: {prompt}
    </input>
  <output>
      Design:
   </output>
</system_context>
        """

    @staticmethod
    def refactor(prompt: str) -> str:
        """Optimize prompt for code refactoring suggestions."""
        return f"""
<system_context>
    <role>
         Your role: Suggest code improvements.
   </role>
    <instructions>
        Focus on:
        - Code quality
        - Performance
        - Readability
        - Best practices
        - Design patterns
    </instructions>
    <input>
        Code to refactor: {prompt}
     </input>
   <output>
        Suggestions:
    </output>
</system_context>
        """

    @staticmethod
    def security(prompt: str) -> str:
        """Optimize prompt for security analysis."""
        return f"""
<system_context>
   <role>
        Your role: Security analysis and fixes.
   </role>
   <instructions>
        Check for:
        - Common vulnerabilities
        - Security best practices
        - Input validation
        - Authentication/Authorization
        - Data protection
    </instructions>
     <input>
       Code to analyze: {prompt}
    </input>
  <output>
        Analysis:
  </output>
</system_context>
        """