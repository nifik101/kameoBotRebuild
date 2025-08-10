#!/bin/bash

# Kameo Bot - Quick Start Script
# This script provides an easy way to start the Kameo Bot application

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo -e "${BLUE}$1${NC}"
}

# Check if Python is available
check_python() {
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is not installed or not in PATH"
        exit 1
    fi
    print_status "Python 3 found: $(python3 --version)"
}

# Check if uv is available
check_uv() {
    if ! command -v uv &> /dev/null; then
        print_error "uv is not installed or not in PATH"
        print_warning "Please install uv:"
        echo "  curl -LsSf https://astral.sh/uv/install.sh | sh"
        echo "  # Or: pip install uv"
        echo "  # Or: brew install uv (macOS)"
        exit 1
    fi
    print_status "uv found: $(uv --version)"
}

# Check if virtual environment exists
check_venv() {
    if [ ! -d ".venv" ]; then
        print_warning "Virtual environment not found. Creating one..."
        uv venv
        print_status "Virtual environment created"
    fi
    
    # Activate virtual environment
    source .venv/bin/activate
    print_status "Virtual environment activated"
}

# Check if dependencies are installed
check_dependencies() {
    if [ ! -f "pyproject.toml" ]; then
        print_error "pyproject.toml not found"
        exit 1
    fi
    
    print_status "Checking dependencies..."
    if ! uv pip show fastapi &> /dev/null; then
        print_warning "Dependencies not installed. Installing..."
        uv sync
        print_status "Dependencies installed"
    else
        print_status "Dependencies already installed"
    fi
}

# Check if .env file exists
check_env() {
    if [ ! -f ".env" ]; then
        print_error ".env file not found"
        print_warning "Please copy .env.example to .env and configure your settings:"
        echo "  cp .env.example .env"
        echo "  # Then edit .env with your Kameo credentials"
        exit 1
    fi
    print_status ".env file found"
}

# Main menu
show_menu() {
    clear
    print_header "🤖 Kameo Bot - Automated Loan Bidding System"
    echo "=================================================="
    echo ""
    echo "Choose an option:"
echo ""
echo "1) Start API Server (Backend)"
echo "2) Start Frontend (React App)"
echo "3) Start Both (API + Frontend)"
echo "4) Start CLI Interface"
echo "5) Run Demo"
echo "6) Validate Configuration"
echo "7) Install Dependencies"
echo "8) Exit"
    echo ""
    read -p "Enter your choice (1-8): " choice
}

# Start API server
start_api() {
    print_header "🚀 Starting API Server"
    echo ""
    read -p "Port (default: 8000): " port
    port=${port:-8000}
    
    read -p "Enable debug mode? (y/N): " debug
    debug_flag=""
    if [[ $debug =~ ^[Yy]$ ]]; then
        debug_flag="--debug"
    fi
    
    print_status "Starting API server on port $port..."
    python run.py --api --port $port $debug_flag
}

# Start Frontend
start_frontend() {
    print_header "🌐 Starting Frontend (React App)"
    echo ""
    
    # Check if Node.js is available
    if ! command -v node &> /dev/null; then
        print_error "Node.js is not installed or not in PATH"
        print_warning "Please install Node.js from https://nodejs.org"
        exit 1
    fi
    print_status "Node.js found: $(node --version)"
    
    # Check if pnpm is available
    if ! command -v pnpm &> /dev/null; then
        print_error "pnpm is not installed or not in PATH"
        print_warning "Please install pnpm:"
        echo "  npm install -g pnpm"
        echo "  # Or: curl -fsSL https://get.pnpm.io/install.sh | sh -"
        echo "  # Or: brew install pnpm (macOS)"
        exit 1
    fi
    print_status "pnpm found: $(pnpm --version)"
    
    # Check if frontend directory exists
    if [ ! -d "frontend" ]; then
        print_error "Frontend directory not found"
        exit 1
    fi
    
    # Navigate to frontend directory
    cd frontend
    
    # Check if node_modules exists
    if [ ! -d "node_modules" ]; then
        print_warning "Frontend dependencies not installed. Installing..."
        pnpm install
        print_status "Frontend dependencies installed"
    fi
    
    print_status "Starting frontend development server..."
    print_status "Frontend will be available at: http://localhost:5173"
    print_status "API proxy configured to: http://localhost:8000"
    echo ""
    
    # Start the frontend
    pnpm run dev
}

# Start both API and Frontend
start_both() {
    print_header "🚀 Starting Both API and Frontend"
    echo ""
    print_status "This will start both the API server and frontend in separate terminals"
    echo ""
    
    # Check if we can open new terminals
    if command -v osascript &> /dev/null; then
        # macOS - use osascript to open new terminal windows
        print_status "Starting API server in new terminal..."
        osascript -e 'tell app "Terminal" to do script "cd '$(pwd)' && python run.py --api"'
        
        sleep 2
        
        print_status "Starting frontend in new terminal..."
        osascript -e 'tell app "Terminal" to do script "cd '$(pwd)' && ./start.sh frontend"'
        
        print_status "✅ Both services started in separate terminals"
        print_status "🌐 Frontend: http://localhost:5173"
        print_status "🔧 API: http://localhost:8000"
        
    elif command -v gnome-terminal &> /dev/null; then
        # Linux - use gnome-terminal
        print_status "Starting API server in new terminal..."
        gnome-terminal -- bash -c "cd $(pwd) && python run.py --api; exec bash"
        
        sleep 2
        
        print_status "Starting frontend in new terminal..."
        gnome-terminal -- bash -c "cd $(pwd) && ./start.sh frontend; exec bash"
        
        print_status "✅ Both services started in separate terminals"
        print_status "🌐 Frontend: http://localhost:5173"
        print_status "🔧 API: http://localhost:8000"
        
    else
        print_warning "Cannot open new terminals automatically"
        print_status "Please start API and frontend manually:"
        echo ""
        echo "Terminal 1: python run.py --api"
        echo "Terminal 2: cd frontend && pnpm run dev"
        echo ""
        print_status "Or use option 1 and 2 separately"
    fi
}

# Start CLI interface
start_cli() {
    print_header "💻 Starting CLI Interface"
    echo ""
    print_status "Starting CLI interface..."
    python run.py --cli
}

# Run demo
run_demo() {
    print_header "🎬 Running Demo"
    echo ""
    print_status "Running Kameo Bot demo..."
    python run.py --demo
}

# Validate configuration
validate_config() {
    print_header "🔧 Validating Configuration"
    echo ""
    print_status "Validating configuration..."
    python run.py --validate-only
}

# Install dependencies
install_deps() {
    print_header "📦 Installing Dependencies"
    echo ""
    print_status "Installing dependencies from pyproject.toml..."
    uv sync
    print_status "Dependencies installed successfully"
}

# Main function
main() {
    print_header "🤖 Kameo Bot - Quick Start"
    echo ""
    
    # Pre-flight checks
    check_python
    check_uv
    check_venv
    check_dependencies
    check_env
    
    echo ""
    print_status "All checks passed! Ready to start."
    echo ""
    
    # Show menu
    while true; do
        show_menu
        
        case $choice in
            1)
                start_api
                break
                ;;
            2)
                start_frontend
                break
                ;;
            3)
                start_both
                break
                ;;
            4)
                start_cli
                break
                ;;
            5)
                run_demo
                break
                ;;
            6)
                validate_config
                echo ""
                read -p "Press Enter to continue..."
                ;;
            7)
                install_deps
                echo ""
                read -p "Press Enter to continue..."
                ;;
            8)
                print_status "Goodbye!"
                exit 0
                ;;
            *)
                print_error "Invalid choice. Please try again."
                sleep 2
                ;;
        esac
    done
}

# Handle command line arguments
if [ $# -eq 0 ]; then
    # No arguments, show interactive menu
    main
else
    # Handle command line arguments
    case $1 in
        "api")
            check_python
            check_uv
            check_venv
            check_dependencies
            check_env
            python run.py --api ${@:2}
            ;;
        "cli")
            check_python
            check_uv
            check_venv
            check_dependencies
            check_env
            python run.py --cli ${@:2}
            ;;
        "demo")
            check_python
            check_uv
            check_venv
            check_dependencies
            check_env
            python run.py --demo ${@:2}
            ;;
        "frontend")
            start_frontend
            ;;
        "validate")
            check_python
            check_uv
            check_venv
            check_dependencies
            check_env
            python run.py --validate-only ${@:2}
            ;;
        "install")
            check_python
            check_venv
            install_deps
            ;;
        *)
            echo "Usage: $0 [api|frontend|both|cli|demo|validate|install] [options]"
            echo ""
            echo "Commands:"
            echo "  api      - Start API server"
            echo "  frontend - Start frontend (React app)"
            echo "  both     - Start both API and frontend"
            echo "  cli      - Start CLI interface"
            echo "  demo     - Run demo"
            echo "  validate - Validate configuration"
            echo "  install  - Install dependencies"
            echo ""
            echo "Examples:"
            echo "  $0 api --port 8080 --debug"
            echo "  $0 frontend"
            echo "  $0 both"
            echo "  $0 cli"
            echo "  $0 demo"
            echo ""
            echo "Or run without arguments for interactive menu"
            exit 1
            ;;
    esac
fi 