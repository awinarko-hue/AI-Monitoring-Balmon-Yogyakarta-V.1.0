import argparse
import uvicorn

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run AI Monitoring Balmon Yogyakarta Server")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Host IP address")
    parser.add_argument("--port", type=int, default=3000, help="Port number (default: 3000)")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload")
    
    args = parser.parse_args()
    
    print(f"==================================================")
    print(f" Starting AI Monitoring Balmon Yogyakarta Server")
    print(f" URL: http://{args.host}:{args.port}/")
    print(f"==================================================")
    
    uvicorn.run("app.main:app", host=args.host, port=args.port, reload=args.reload)
