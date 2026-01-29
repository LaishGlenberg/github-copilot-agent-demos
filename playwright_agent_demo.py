import asyncio
import sys
from copilot import CopilotClient
from copilot.generated.session_events import SessionEventType

async def main():
    client = CopilotClient()
  
    #Might need to use full path to the copilot CLI installation if getting "file not found" errors
    #client = CopilotClient(options={
    #    "cli_path": r"path\to\copilot\copilot.bat" or "copilot.cmd"
    #})
    
    await client.start()
    
    # Create readline-like interface for Python
    verbose = False
    
    session = await client.create_session({
        "model": "gpt-4.1",
        "mcp_servers": {
            "playwright": {
                "type": "stdio",
                "command": "npx",
                "args": ["-y", "@playwright/mcp@latest"],
                "tools": ["*"],
            }
        },
        "system_message": {
            "content": "You are a browser automation assistant. DO NOT USE POWERSHELL",
        },
        "excluded_tools": ["powershell"],
        "on_permission_request": lambda req, ctx: {"kind": "approved"},  # Always approve for now
    })
    
    def handle_event(event):
        if event.type == SessionEventType.SESSION_INFO:
            print(f"\n[session info] {getattr(event.data, 'message', '')}")
        
        elif event.type == SessionEventType.SESSION_ERROR:
            print(f"\n[session error] {getattr(event.data, 'message', '')}")
        
        elif event.type == SessionEventType.TOOL_EXECUTION_START:
            tool_name = getattr(event.data, 'tool_name', '')
            tool_call_id = getattr(event.data, 'tool_call_id', '')
            args = getattr(event.data, 'arguments', {})
            if verbose:
                print(f"\n[tool start] {tool_name} id={tool_call_id} args={args}")
            else:
                print(f"\n[tool start] {tool_name}")
        
        elif event.type == SessionEventType.TOOL_EXECUTION_PARTIAL_RESULT:
            tool_call_id = getattr(event.data, 'tool_call_id', '')
            partial_output = getattr(event.data, 'partial_output', '')
            if verbose:
                print(f"[tool partial] id={tool_call_id} {partial_output}")
        
        elif event.type == SessionEventType.TOOL_EXECUTION_PROGRESS:
            tool_call_id = getattr(event.data, 'tool_call_id', '')
            progress_message = getattr(event.data, 'progress_message', '')
            if verbose:
                print(f"[tool progress] id={tool_call_id} {progress_message}")
        
        elif event.type == SessionEventType.TOOL_EXECUTION_COMPLETE:
            tool_call_id = getattr(event.data, 'tool_call_id', '')
            success = getattr(event.data, 'success', False)
            result = getattr(event.data, 'result', None)
            error = getattr(event.data, 'error', None)
            output = getattr(result, 'content', '') if result else getattr(error, 'message', '(no content)')
            if verbose:
                print(f"[tool done] id={tool_call_id} success={success}\n{output}")
            else:
                print(f"[tool done] id={tool_call_id} success={success}")
        
        elif event.type == SessionEventType.ASSISTANT_MESSAGE:
            print(f"\n[assistant]\n{event.data.content}")
    
    session.on(handle_event)
    
    async def ask(prompt, timeout_ms=120000):
        return await session.send_and_wait({"prompt": prompt}, timeout_ms)
    
    try:
        print("Interactive Mode started. Type 'exit' to quit or 'verbose' to toggle logs")
        
        while True:
            try:
                prompt_input = input("\nCommand Agent > ")
                
                if prompt_input.lower() in ["exit", "quit"]:
                    break
                
                if prompt_input.lower() == "verbose":
                    verbose = not verbose
                    print(f'verbose mode: {verbose}')
                    continue
                
                if not prompt_input.strip():
                    continue
                
                try:
                    await ask(prompt_input)
                except Exception as err:
                    print(f"[Execution Error]: {str(err)}")
            
            except KeyboardInterrupt:
                print("\nExiting...")
                break
            except EOFError:
                print("\nExiting...")
                break
    
    finally:
        await session.destroy()
        await client.stop()

if __name__ == "__main__":
    asyncio.run(main())
