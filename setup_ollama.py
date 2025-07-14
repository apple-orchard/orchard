#!/usr/bin/env python3
"""
Setup script to help users get started with Ollama for the RAG system
"""

import subprocess
import sys
import time
import requests
import json

def run_command(command, check=True):
    """Run a shell command and return the result"""
    try:
        result = subprocess.run(command, shell=True, check=check, capture_output=True, text=True)
        return result.stdout.strip(), result.stderr.strip(), result.returncode
    except subprocess.CalledProcessError as e:
        return e.stdout.strip(), e.stderr.strip(), e.returncode

def check_ollama_installed():
    """Check if Ollama is installed"""
    stdout, stderr, returncode = run_command("ollama --version", check=False)
    if returncode == 0:
        print(f"✅ Ollama is installed: {stdout}")
        return True
    else:
        print("❌ Ollama is not installed")
        return False

def check_ollama_running():
    """Check if Ollama server is running"""
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            print("✅ Ollama server is running")
            return True
        else:
            print("❌ Ollama server is not responding")
            return False
    except requests.exceptions.RequestException:
        print("❌ Ollama server is not running")
        return False

def list_models():
    """List available models"""
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            models = response.json()
            if models.get('models'):
                print("📚 Available models:")
                for model in models['models']:
                    print(f"  - {model['name']}")
                return [model['name'] for model in models['models']]
            else:
                print("📚 No models installed")
                return []
        else:
            print("❌ Failed to list models")
            return []
    except requests.exceptions.RequestException as e:
        print(f"❌ Error listing models: {e}")
        return []

def pull_model(model_name):
    """Pull a model from Ollama"""
    print(f"📥 Pulling model: {model_name}")
    stdout, stderr, returncode = run_command(f"ollama pull {model_name}", check=False)
    
    if returncode == 0:
        print(f"✅ Successfully pulled model: {model_name}")
        return True
    else:
        print(f"❌ Failed to pull model: {model_name}")
        print(f"Error: {stderr}")
        return False

def install_ollama():
    """Provide instructions to install Ollama"""
    print("\n🔧 To install Ollama, please visit: https://ollama.com/download")
    print("\nOr use these commands:")
    print("  macOS: brew install ollama")
    print("  Linux: curl -fsSL https://ollama.com/install.sh | sh")
    print("  Windows: Download from https://ollama.com/download/windows")
    print("\nAfter installation, run: ollama serve")

def main():
    """Main setup function"""
    print("🚀 Ollama Setup for RAG System")
    print("=" * 50)
    
    # Check if Ollama is installed
    if not check_ollama_installed():
        install_ollama()
        return
    
    # Check if Ollama server is running
    if not check_ollama_running():
        print("\n💡 To start Ollama server, run: ollama serve")
        print("Then run this script again.")
        return
    
    # List current models
    models = list_models()
    
    # Check if recommended model is available
    recommended_model = "llama3.1:8b"
    if recommended_model not in models:
        print(f"\n🎯 Recommended model '{recommended_model}' not found")
        response = input(f"Would you like to pull {recommended_model}? (y/n): ").lower()
        
        if response == 'y':
            if pull_model(recommended_model):
                print(f"✅ Model {recommended_model} is ready!")
            else:
                print(f"❌ Failed to pull {recommended_model}")
                return
        else:
            print("⚠️  You can pull it later with: ollama pull llama3.1:8b")
    else:
        print(f"✅ Recommended model '{recommended_model}' is available")
    
    # Test the model
    print(f"\n🧪 Testing model: {recommended_model}")
    stdout, stderr, returncode = run_command(f'ollama run {recommended_model} "Hello, respond with just OK"', check=False)
    
    if returncode == 0:
        print("✅ Model test successful!")
        print(f"Response: {stdout}")
    else:
        print("❌ Model test failed")
        print(f"Error: {stderr}")
    
    print("\n🎉 Ollama setup complete!")
    print("You can now start the RAG system with: python main.py")

if __name__ == "__main__":
    main() 