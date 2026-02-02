"""CLI tool for agent-tax-toolkit."""

import sys
import os
from cryptography.fernet import Fernet


def main():
    """Main CLI entry point."""
    if len(sys.argv) < 2:
        print_help()
        return
    
    command = sys.argv[1]
    
    if command == "init":
        init_config()
    elif command == "generate-key":
        generate_encryption_key()
    elif command == "serve":
        serve()
    elif command == "help" or command == "--help" or command == "-h":
        print_help()
    else:
        print(f"Unknown command: {command}")
        print_help()


def print_help():
    """Print CLI help."""
    help_text = """
Agent Tax Toolkit - CLI

Commands:
  init            Initialize configuration (create .env file)
  generate-key    Generate encryption key for TINs
  serve           Start W-9 portal server
  help            Show this help message

Examples:
  agent-tax init
  agent-tax generate-key
  agent-tax serve --port 8000
"""
    print(help_text)


def generate_encryption_key():
    """Generate and print encryption key."""
    key = Fernet.generate_key()
    print("\n🔐 Generated TIN Encryption Key:")
    print(key.decode())
    print("\n⚠️  Store this securely! Add to .env file:")
    print(f"TIN_ENCRYPTION_KEY={key.decode()}")
    print()


def init_config():
    """Initialize .env configuration file."""
    if os.path.exists(".env"):
        response = input(".env file already exists. Overwrite? (y/N): ")
        if response.lower() != "y":
            print("Aborted.")
            return
    
    # Generate encryption key
    key = Fernet.generate_key()
    
    env_content = f"""# Agent Tax Toolkit Configuration

# Database URL (SQLite by default, use PostgreSQL for production)
DATABASE_URL=sqlite:///./agent_tax.db

# TIN Encryption Key (KEEP SECRET!)
TIN_ENCRYPTION_KEY={key.decode()}

# Email Configuration (for W-9 reminders)
# SMTP_HOST=smtp.gmail.com
# SMTP_PORT=587
# SMTP_USER=your-email@gmail.com
# SMTP_PASSWORD=your-app-password
# SMTP_FROM=your-email@gmail.com

# Stripe API Key (for payment data)
# STRIPE_API_KEY=sk_test_...

# IRS TIN (for 1099 filing)
# IRS_TIN=12-3456789
"""
    
    with open(".env", "w") as f:
        f.write(env_content)
    
    print("✅ Created .env file with encryption key")
    print("📝 Edit .env to add Stripe/email credentials")


def serve():
    """Start FastAPI server."""
    import uvicorn
    from .api import app
    
    # Check if .env exists
    if not os.path.exists(".env"):
        print("❌ No .env file found. Run 'agent-tax init' first.")
        return
    
    # Load .env
    from dotenv import load_dotenv
    load_dotenv()
    
    # Parse port from args
    port = 8000
    if "--port" in sys.argv:
        try:
            port_idx = sys.argv.index("--port")
            port = int(sys.argv[port_idx + 1])
        except (IndexError, ValueError):
            print("Invalid --port argument. Using default: 8000")
    
    print(f"\n🚀 Starting W-9 Portal on http://localhost:{port}")
    print("📋 API Docs: http://localhost:{port}/docs\n")
    
    uvicorn.run(app, host="0.0.0.0", port=port)


if __name__ == "__main__":
    main()
