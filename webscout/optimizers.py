"""Prompt optimization utilities."""
import platform
import subprocess
import os

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
    def code(prompt):
        """Deprecated: Use coder() instead"""
        return Optimizers.coder(prompt)

    @staticmethod
    def shell_command(prompt):
        """Deprecated: Use coder() instead"""
        return Optimizers.coder(f"!{prompt}")

    @staticmethod
    def coder(prompt):
        """Unified optimizer for both code and shell commands."""
        # Get system info for shell commands
        operating_system = ""
        if platform.system() == "Windows":
            operating_system = "Windows"
        elif platform.system() == "Darwin":
            operating_system = "MacOS"
        elif platform.system() == "Linux":
            try:
                result = subprocess.check_output(["lsb_release", "-si"]).decode().strip()
                operating_system = f"Linux/{result}" if result else "Linux"
            except:
                operating_system = "Linux"
        else:
            operating_system = platform.system()

        # Get shell info
        shell_name = "/bin/sh"
        if platform.system() == "Windows":
            shell_name = "powershell.exe" if os.getenv("PSModulePath") else "cmd.exe"
        else:
            shell_env = os.getenv("SHELL")
            if shell_env:
                shell_name = shell_env

        return (
            "Your Role: You are a code generation expert. Analyze the request and provide appropriate output.\n"
            "If the request starts with '!' or involves system/shell operations, provide a shell command.\n"
            "Otherwise, provide Python code.\n\n"
            "RULES:\n"
            "1. Provide ONLY code/command output without any description or markdown\n"
            "2. For shell commands:\n"
            f"   - Target OS: {operating_system}\n"
            f"   - Shell: {shell_name}\n"
            "   - Combine multiple steps when possible\n"
            "3. For Python code:\n"
            "   - Include necessary imports\n"
            "   - Handle errors appropriately\n"
            "   - Follow PEP 8 style\n"
            "4. If details are missing, use most logical implementation\n"
            "5. No warnings, descriptions, or explanations\n\n"
            f"Request: {prompt}\n"
            "Output:\n"
        )

    @staticmethod
    def search(prompt):
        """Optimize prompt for web search queries."""
        return (
            "Your role: Generate a precise and focused web search query.\n"
            "IMPORTANT: Return only the search query without any explanation.\n"
            "Format: Plain text, no markdown.\n"
            "If details are missing, focus on the most relevant aspects.\n\n"
            f"Request: {prompt}\n"
            "Search Query:"
        )

    @staticmethod
    def math(prompt):
        """Optimize prompt for mathematical problem solving."""
        return (
            "Your role: Solve mathematical problems step by step.\n"
            "Format: Plain text, show calculations clearly.\n"
            "Show all steps and intermediate results.\n"
            "Include units where applicable.\n"
            "Provide final answer in a clear format.\n\n"
            f"Problem: {prompt}\n"
            "Solution:"
        )

    @staticmethod
    def explain(prompt):
        """Optimize prompt for clear explanations."""
        return (
            "Your role: Explain concepts clearly and concisely.\n"
            "Format: Break down complex ideas into simple terms.\n"
            "Use analogies where helpful.\n"
            "Focus on key points and practical understanding.\n\n"
            f"Topic: {prompt}\n"
            "Explanation:"
        )

    @staticmethod
    def debug(prompt):
        """Optimize prompt for debugging code."""
        return (
            "Your role: Debug code and identify issues.\n"
            "Steps:\n"
            "1. Identify syntax errors\n"
            "2. Check logic issues\n"
            "3. Look for common pitfalls\n"
            "4. Suggest fixes\n\n"
            f"Code to debug: {prompt}\n"
            "Analysis:"
        )

    @staticmethod
    def api(prompt):
        """Optimize prompt for API endpoint design."""
        return (
            "Your role: Design RESTful API endpoints.\n"
            "Include:\n"
            "- HTTP methods\n"
            "- URL structure\n"
            "- Request/Response format\n"
            "- Status codes\n\n"
            f"API requirement: {prompt}\n"
            "Design:"
        )

    @staticmethod
    def sql(prompt):
        """Optimize prompt for SQL query generation."""
        return (
            "Your role: Generate optimized SQL queries.\n"
            "Requirements:\n"
            "- Standard SQL syntax\n"
            "- Efficient query structure\n"
            "- Proper joins and indexing\n"
            "- Consider performance\n\n"
            f"Query need: {prompt}\n"
            "SQL:"
        )

    @staticmethod
    def regex(prompt):
        """Optimize prompt for regex pattern generation."""
        return (
            "Your role: Generate precise regex patterns.\n"
            "Requirements:\n"
            "- Standard regex syntax\n"
            "- Pattern explanation\n"
            "- Test cases\n"
            "- Consider edge cases\n\n"
            f"Pattern need: {prompt}\n"
            "Regex:"
        )

    @staticmethod
    def test(prompt):
        """Optimize prompt for test case generation."""
        return (
            "Your role: Generate comprehensive test cases.\n"
            "Include:\n"
            "- Edge cases\n"
            "- Corner cases\n"
            "- Error scenarios\n"
            "- Happy path\n"
            "Format: Test name and expected result\n\n"
            f"Test requirement: {prompt}\n"
            "Test Cases:"
        )

    @staticmethod
    def docker(prompt):
        """Optimize prompt for Dockerfile creation."""
        return (
            "Your role: Create efficient Dockerfile.\n"
            "Consider:\n"
            "- Base image selection\n"
            "- Layer optimization\n"
            "- Security best practices\n"
            "- Multi-stage builds if needed\n\n"
            f"Container requirement: {prompt}\n"
            "Dockerfile:"
        )

    @staticmethod
    def git(prompt):
        """Optimize prompt for git commands."""
        return (
            "Your role: Generate git commands.\n"
            "Requirements:\n"
            "- Clear and safe commands\n"
            "- Consider current state\n"
            "- Include safety checks\n"
            "- Best practices\n\n"
            f"Git task: {prompt}\n"
            "Command:"
        )

    @staticmethod
    def yaml(prompt):
        """Optimize prompt for YAML configuration."""
        return (
            "Your role: Generate YAML configuration.\n"
            "Requirements:\n"
            "- Valid YAML syntax\n"
            "- Clear structure\n"
            "- Comments for complex parts\n"
            "- Best practices\n\n"
            f"Config need: {prompt}\n"
            "YAML:"
        )

    @staticmethod
    def cli(prompt):
        """Optimize prompt for CLI command design."""
        return (
            "Your role: Design CLI commands.\n"
            "Include:\n"
            "- Command structure\n"
            "- Arguments/options\n"
            "- Help messages\n"
            "- Examples\n\n"
            f"CLI requirement: {prompt}\n"
            "Design:"
        )

    @staticmethod
    def refactor(prompt):
        """Optimize prompt for code refactoring suggestions."""
        return (
            "Your role: Suggest code improvements.\n"
            "Focus on:\n"
            "- Code quality\n"
            "- Performance\n"
            "- Readability\n"
            "- Best practices\n"
            "- Design patterns\n\n"
            f"Code to refactor: {prompt}\n"
            "Suggestions:"
        )

    @staticmethod
    def security(prompt):
        """Optimize prompt for security analysis."""
        return (
            "Your role: Security analysis and fixes.\n"
            "Check for:\n"
            "- Common vulnerabilities\n"
            "- Security best practices\n"
            "- Input validation\n"
            "- Authentication/Authorization\n"
            "- Data protection\n\n"
            f"Code to analyze: {prompt}\n"
            "Analysis:"
        )