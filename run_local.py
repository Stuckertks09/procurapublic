import asyncio
import uvicorn
import subprocess
import sys
import os

# FastAPI app import
from backend.main import app

async def start_agents():
    print("🚀 Starting agents as separate processes...\n")
    
    agent_scripts = [
        ("agents/orchestrator.py", "orchestrator_agent"),
        ("agents/scout.py", "scout_agent"),
        ("agents/compute_agent.py", "compute_agent"),   # ✅ NEW LINE
        ("agents/evaluator.py", "evaluator_agent"),
        ("agents/negotiator.py", "negotiator_agent")
    ]
    
    processes = []
    
    # Set up environment with proper PYTHONPATH
    env = os.environ.copy()
    project_root = os.getcwd()
    env['PYTHONPATH'] = project_root
    
    for script, name in agent_scripts:
        script_path = os.path.join(project_root, script)
        
        # Check if file exists
        if not os.path.exists(script_path):
            print(f"❌ Script not found: {script_path}")
            continue
            
        print(f"🚀 Starting {name} from {script}...")
        
        # Start agent as subprocess with proper error handling
        try:
            process = subprocess.Popen(
                [sys.executable, script_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                cwd=project_root,
                env=env  # Pass environment with PYTHONPATH
            )
            processes.append((process, name, script))
            
            # Wait for agent to start and register
            print(f"⏳ Waiting for {name} to register (10 seconds)...")
            await asyncio.sleep(10)
            
            # Check if process is still running
            if process.poll() is None:
                print(f"✅ {name} is running\n")
            else:
                # Process died, print error
                stdout, stderr = process.communicate()
                print(f"❌ {name} failed to start!")
                if stderr:
                    print(f"   Error output:\n{stderr}")
                if stdout:
                    print(f"   Standard output:\n{stdout}")
                print()
                
        except Exception as e:
            print(f"❌ Failed to start {name}: {e}\n")
    
    print("✅ Agent startup phase complete!")
    print(f"✅ {len([p for p, _, _ in processes if p.poll() is None])} agents running")
    print("=" * 80 + "\n")
    
    # Keep monitoring processes
    while True:
        await asyncio.sleep(10)
        for process, name, script in processes:
            if process.poll() is not None:
                print(f"⚠️ {name} has stopped unexpectedly!")

async def start_fastapi():
    # Wait for agents to start first
    print("⏳ Waiting 5 seconds before starting FastAPI...\n")
    await asyncio.sleep(5)
    
    print("🌐 Starting FastAPI on http://127.0.0.1:9000\n")
    config = uvicorn.Config(app, host="127.0.0.1", port=9000, reload=False, log_level="info")
    server = uvicorn.Server(config)
    await server.serve()

async def main():
    await asyncio.gather(
        start_agents(),
        start_fastapi()
    )

if __name__ == "__main__":
    print("\n===================================")
    print("🔥 Local Multi-Agent Orchestration 🔥")
    print("===================================\n")
    
    # Verify we're in the right directory
    print(f"Working directory: {os.getcwd()}\n")
    
    asyncio.run(main())
