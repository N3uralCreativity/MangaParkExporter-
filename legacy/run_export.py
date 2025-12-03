"""
Export runner script for Electron app
Communicates via JSON stdout
"""

import sys
import json
from datetime import datetime
import backend_export

def log_progress(percent, step, log_entry):
    """Send progress update as JSON to stdout"""
    output = {
        "percent": percent,
        "step": step,
        "log": log_entry
    }
    print(json.dumps(output), flush=True)

if __name__ == '__main__':
    try:
        # Get cookies from command line argument
        cookies_json = sys.argv[1]
        cookies = json.loads(cookies_json)
        
        # Run export
        result = backend_export.export_mangapark(cookies, log_progress)
        
        # Send final result
        output = {
            "status": result["status"],
            "result": result
        }
        print(json.dumps(output), flush=True)
        
    except Exception as e:
        error_output = {
            "status": "error",
            "log": {
                "type": "error",
                "message": f"Fatal error: {str(e)}",
                "time": datetime.now().strftime("%H:%M:%S")
            }
        }
        print(json.dumps(error_output), flush=True)
        sys.exit(1)
