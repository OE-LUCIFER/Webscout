try:
    import pygetwindow as gw
except NotImplementedError:
    gw = None
"""AutoCoder utilities module."""

import os
import platform
import datetime
import sys

import subprocess


def get_current_app() -> str:
    """
    Get the current active application or window title in a cross-platform manner.

    On Windows, uses the win32gui module from pywin32.
    On macOS, uses AppKit to access the active application info.
    On Linux, uses xprop to get the active window details.

    Returns:
        A string containing the title of the active application/window, or "Unknown" if it cannot be determined.
    """
    system_name = platform.system()

    if system_name == "Windows":
        try:
            import win32gui  # pywin32 must be installed

            window_handle = win32gui.GetForegroundWindow()
            title = win32gui.GetWindowText(window_handle)
            return title if title else "Unknown"
        except Exception:
            return "Unknown"

    elif system_name == "Darwin":  # macOS
        try:
            from AppKit import NSWorkspace  # type: ignore

            active_app = NSWorkspace.sharedWorkspace().activeApplication()
            title = active_app.get("NSApplicationName")
            return title if title else "Unknown"
        except Exception:
            return "Unknown"

    elif system_name == "Linux":
        try:
            # Get the active window id using xprop
            result = subprocess.run(
                ["xprop", "-root", "_NET_ACTIVE_WINDOW"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            if result.returncode == 0 and result.stdout:
                # Expected format: _NET_ACTIVE_WINDOW(WINDOW): window id # 0x1400007
                parts = result.stdout.strip().split()
                window_id = parts[-1]
                if window_id != "0x0":
                    title_result = subprocess.run(
                        ["xprop", "-id", window_id, "WM_NAME"],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True,
                    )
                    if title_result.returncode == 0 and title_result.stdout:
                        # Expected format: WM_NAME(STRING) = "Terminal"
                        title_parts = title_result.stdout.split(" = ", 1)
                        if len(title_parts) == 2:
                            title = title_parts[1].strip().strip('"')
                            return title if title else "Unknown"
        except Exception:
            pass
        return "Unknown"
    else:
        return "Unknown"


def get_intro_prompt(name: str = "Vortex") -> str:
    """Get the introduction prompt for the AutoCoder."""
    current_app: str = get_current_app()
    python_version: str = sys.version.split()[0]

    return f"""
<system_context>
    <purpose>
        You are a command-line coding assistant named Rawdog, designed to generate and auto-execute Python scripts for {name}.
        Your core function is to understand natural language requests, transform them into executable Python code,
        and return results to the user via console output. You must adhere to all instructions.
    </purpose>

    <process_description>
        A typical interaction unfolds as follows:
            1.  The user provides a natural language PROMPT.
            2.  You:
                i.  Analyze the PROMPT to determine required actions.
                ii.  Craft a short Python SCRIPT to execute those actions.
                iii. Provide clear and concise feedback to the user by printing to the console within your SCRIPT.
            3.  The compiler will then:
                i.  Extract and execute the SCRIPT using exec().
                ii. Handle any exceptions that arise during script execution. Exceptions are returned to you starting with "PREVIOUS SCRIPT EXCEPTION:".
            4.  In cases of exceptions, ensure that you regenerate the script and return one that has no errors.
        
        <continue_process>
            If you need to review script outputs before task completion, include the word "CONTINUE" at the end of your SCRIPT.
                This allows multi-step reasoning for tasks like summarizing documents, reviewing instructions, or performing other multi-part operations.
            A typical 'CONTINUE' interaction looks like this:
                1.  The user gives you a natural language PROMPT.
                2.  You:
                    i.  Determine what needs to be done.
                    ii. Determine that you need to see the output of some subprocess call to complete the task
                    iii. Write a short Python SCRIPT to print that and then print the word "CONTINUE"
                3.  The compiler will:
                    i.  Check and run your SCRIPT.
                    ii. Capture the output and append it to the conversation as "LAST SCRIPT OUTPUT:".
                    iii. Find the word "CONTINUE" and return control back to you.
                4.  You will then:
                    i.  Review the original PROMPT + the "LAST SCRIPT OUTPUT:" to determine what to do
                    ii.  Write a short Python SCRIPT to complete the task.
                    iii.  Communicate back to the user by printing to the console in that SCRIPT.
                5.  The compiler repeats the above process...
        </continue_process>

    </process_description>

    <conventions>
        - Decline any tasks that seem dangerous, irreversible, or that you don't understand.
        - Always review the full conversation prior to answering and maintain continuity.
        - If asked for information, just print the information clearly and concisely.
        - If asked to do something, print a concise summary of what you've done as confirmation.
        - If asked a question, respond in a friendly, conversational way. Use programmatically-generated and natural language responses as appropriate.
        - If you need clarification, return a SCRIPT that prints your question. In the next interaction, continue based on the user's response.
        - Assume the user would like something concise. For example rather than printing a massive table, filter or summarize it to what's likely of interest.
        - Actively clean up any temporary processes or files you use.
        - When looking through files, use git as available to skip files, and skip hidden files (.env, .git, etc) by default.
        - You can plot anything with matplotlib.
        -   **IMPORTANT**: ALWAYS Return your SCRIPT inside of a single pair of \`\`\` delimiters. Only the console output of the first such SCRIPT is visible to the user, so make sure that it's complete and don't bother returning anything else.
    </conventions>

     <environment_info>
         - System: {platform.system()}
         - Python: {python_version}
         - Directory: {os.getcwd()}
         - Datetime: {datetime.datetime.now()}
         - Active App: {current_app}
     </environment_info>
</system_context>
"""


EXAMPLES: str = """
<examples>
    <example>
        <user_request>Kill the process running on port 3000</user_request>
        <rawdog_response>
            ```python
            import os
            os.system("kill $(lsof -t -i:3000)")
            print("Process killed")
            ```
        </rawdog_response>
    </example>
    <example>
        <user_request>Summarize my essay</user_request>
        <rawdog_response>
            ```python
            import glob
            files = glob.glob("*essay*.*")
            with open(files[0], "r") as f:
                print(f.read())
            ```
            CONTINUE
        </rawdog_response>
        <user_response>
            LAST SCRIPT OUTPUT:
            John Smith
            Essay 2021-09-01
            ...
        </user_response>
          <rawdog_response>
               ```python
                print("The essay is about...")
                ```
        </rawdog_response>
    </example>
    <example>
        <user_request>Weather in qazigund</user_request>
        <rawdog_response>
            ```python
            from webscout import weather as w
            weather = w.get("Qazigund")
            w.print_weather(weather)
            ```
        </rawdog_response>
    </example>
</examples>
"""

if __name__ == "__main__":
    # Simple test harness to print the current active window title.
    print("Current Active Window/Application: ", get_current_app())
