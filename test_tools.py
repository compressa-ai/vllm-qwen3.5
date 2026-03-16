"""
Test function calling with tools usage.
"""

from openai import OpenAI
import os
import json


import sys
import io

def exec_user_code(code, test_cases):
    local_vars = {}
    old_stdout = sys.stdout
    old_stderr = sys.stderr
    sys.stdout = io.StringIO()
    sys.stderr = io.StringIO()
    try:
        exec(code, local_vars)
        func_name = None
        for name in local_vars:
            if callable(local_vars[name]) and "palindrome" in name.lower():
                func_name = name
                break
        assert func_name is not None, "No palindrome function found in generated code!"
        results = []
        for case in test_cases:
            try:
                result = local_vars[func_name](case)
                results.append((case, result))
            except Exception as e:
                results.append((case, f"Exception: {e}"))
        out = sys.stdout.getvalue()
        err = sys.stderr.getvalue()
        return {"stdout": out, "stderr": err, "results": results}
    except Exception as e:
        return {"stdout": sys.stdout.getvalue(), "stderr": sys.stderr.getvalue() + str(e), "results": []}
    finally:
        sys.stdout = old_stdout
        sys.stderr = old_stderr



def test_tools():
    print("\n","Testing tools usage".center(80, "="), "\n")
    url = f"http://localhost:10010/v1/"
    client = OpenAI(
        base_url=url,
        api_key="TOKEN_1"
    )
    tools = [
        {
        "type": "function",
        "function": {
            "name": "python_code",
            "description": "Prepares python code for execution.",
            "parameters": {
                "type": "object",
                "properties": {
                    "code": {"type": "string", "description": "Python code for execution"}
                },
                "required": ["code"]
            }
        }
        }
        ]
    user_request = "Write a function that checks if a string is a palindrome, and test it (not more than 3 examples)."
    cases = ["madam", "", "a man a plan a canal panama", "banana"]
    messages = [
    {"role": "user", "content": user_request}]
    MAX_ATTEMPTS = 3

    print(f"User request - {user_request}\n\n")
    print(f"Cases - {cases}\n\n")
    attempt = 0
    success = False

    while attempt < MAX_ATTEMPTS and not success:
        attempt += 1
        print(f"\n========== TRY {attempt} ==========\n")
        try:
            response = client.chat.completions.create(
            model="Qwen/Qwen3.5-35B-A3B-FP8",
            messages=messages,
            tools=tools,
            tool_choice="auto",
            extra_body={"chat_template_kwargs": {"thinking": False}},
            )
        except Exception as e:
            assert False, f"Model is deployed without tools, {e}"
        try:
            tool_call = response.choices[0].message.tool_calls[0]
        except:
            print("Tool call failed, retry...")
            continue
        assert tool_call.function.name == tools[0]['function']['name'], "Tool call name is not equal to the tool name"
        args = json.loads(tool_call.function.arguments)
        assert tools[0]['function']['parameters']['properties'].keys() == args.keys(), "Tool call arguments keys are not equal to the tool parameters properties keys"

        user_code = args["code"]
        print("Prepared code:\n")
        print(user_code)
        print("-" * 80, "\n")

        result = exec_user_code(user_code, cases)
        print("Execution result:\n")
        print(result)
        print("-" * 80, "\n")
        expected = [
            ("madam", True),
            ("", True),
            ("a man a plan a canal panama", True),
            ("banana", False),
        ]
        passed = True
        for (input_str, expected_output), (tested_str, got_output) in zip(expected, result["results"]):
            if got_output != expected_output:
                print(f"Failed: {tested_str!r} -> {got_output!r} (expected {expected_output!r})")
                passed = False

        if passed:
            print("All tests passed!")
            success = True
            break
        else:
            fail_report = "Your code did not pass the following tests:\n"
            for (input_str, expected_output), (tested_str, got_output) in zip(expected, result["results"]):
                if got_output != expected_output:
                    fail_report += f"Test case: {repr(tested_str)}. Got: {got_output!r}, expected: {expected_output!r}\n"
            fail_report += "\nFix the code so that all tests pass."
            messages.append(
                {"role": "assistant", "content": None, "tool_calls": [tool_call.model_dump()]}
            )
            messages.append(
                {"role": "tool", "tool_call_id": tool_call.id, "name": tool_call.function.name, "content": json.dumps(result)}
            )
            messages.append({"role": "user", "content": fail_report})

    if not success:
        print(f"\nModel Qwen/Qwen3.5-35B-A3B-FP8 did not generate correct code after 3 attempts.")


if __name__ == "__main__":
    test_tools()