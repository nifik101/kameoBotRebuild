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

# Check if virtual environment exists
check_venv() {
    if [ ! -d ".venv" ]; then
        print_warning "Virtual environment not found. Creating one..."
        python3 -m venv .venv
        print_status "Virtual environment created"
    fi
    
    # Activate virtual environment
    source .venv/bin/activate
    print_status "Virtual environment activated"
}

# Check if dependencies are installed
check_dependencies() {
    if [ ! -f "requirements.txt" ]; then
        print_error "requirements.txt not found"
        exit 1
    fi
    
    print_status "Checking dependencies..."
    if ! pip show fastapi &> /dev/null; then
        print_warning "Dependencies not installed. Installing..."
        pip install -r requirements.txt
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
    echo "1) Start API Server (Web Interface)"
    echo "2) Start CLI Interface"
    echo "3) Run Demo"
    echo "4) Validate Configuration"
    echo "5) Install Dependencies"
    echo "6) Exit"
    echo ""
    read -p "Enter your choice (1-6): " choice
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
    print_status "Installing dependencies from requirements.txt..."
    pip install -r requirements.txt
    print_status "Dependencies installed successfully"
}

# Main function
main() {
    print_header "🤖 Kameo Bot - Quick Start"
    echo ""
    
    # Pre-flight checks
    check_python
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
                start_cli
                break
                ;;
            3)
                run_demo
                break
                ;;
            4)
                validate_config
                echo ""
                read -p "Press Enter to continue..."
                ;;
            5)
                install_deps
                echo ""
                read -p "Press Enter to continue..."
                ;;
            6)
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
            check_venv
            check_dependencies
            check_env
            python run.py --api ${@:2}
            ;;
        "cli")
            check_python
            check_venv
            check_dependencies
            check_env
            python run.py --cli ${@:2}
            ;;
        "demo")
            check_python
            check_venv
            check_dependencies
            check_env
            python run.py --demo ${@:2}
            ;;
        "validate")
            check_python
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
            echo "Usage: $0 [api|cli|demo|validate|install] [options]"
            echo ""
            echo "Commands:"
            echo "  api      - Start API server"
            echo "  cli      - Start CLI interface"
            echo "  demo     - Run demo"
            echo "  validate - Validate configuration"
            echo "  install  - Install dependencies"
            echo ""
            echo "Examples:"
            echo "  $0 api --port 8080 --debug"
            echo "  $0 cli"
            echo "  $0 demo"
            echo ""
            echo "Or run without arguments for interactive menu"
            exit 1
            ;;
    esac
fi 