"""
CLI Helper Functions
"""
import requests
import json
import sys
from typing import Dict, Any, Optional, List
from pathlib import Path


class APIClient:
    """Helper class for making API calls to the RAG system"""
    
    def __init__(self, base_url: str = "http://localhost:8011"):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'Orchard-CLI/1.0.0'
        })
    
    def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make an HTTP request to the API"""
        url = f"{self.base_url}{endpoint}"
        try:
            response = self.session.request(method, url, **kwargs)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"API request failed: {e}")
    
    def get(self, endpoint: str) -> Dict[str, Any]:
        """Make a GET request"""
        return self._make_request('GET', endpoint)
    
    def post(self, endpoint: str, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make a POST request"""
        kwargs = {}
        if data:
            kwargs['json'] = data
        return self._make_request('POST', endpoint, **kwargs)
    
    def put(self, endpoint: str, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make a PUT request"""
        kwargs = {}
        if data:
            kwargs['json'] = data
        return self._make_request('PUT', endpoint, **kwargs)


class ConfigHelper:
    """Helper for managing configuration files"""
    
    @staticmethod
    def load_config(config_path: str = "rag_config.jsonc") -> Dict[str, Any]:
        """Load configuration from JSONC file"""
        try:
            with open(config_path, 'r') as f:
                content = f.read()
                # Simple JSONC parsing (remove comments)
                lines = content.split('\n')
                cleaned_lines = []
                for line in lines:
                    # Remove single-line comments
                    if '//' in line:
                        line = line.split('//')[0]
                    cleaned_lines.append(line)
                cleaned_content = '\n'.join(cleaned_lines)
                return json.loads(cleaned_content)
        except FileNotFoundError:
            raise Exception(f"Configuration file not found: {config_path}")
        except json.JSONDecodeError as e:
            raise Exception(f"Invalid JSON in config file: {e}")
    
    @staticmethod
    def save_config(config: Dict[str, Any], config_path: str = "rag_config.jsonc") -> None:
        """Save configuration to JSONC file"""
        try:
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=2)
        except Exception as e:
            raise Exception(f"Failed to save config: {e}")


class DisplayHelper:
    """Helper for formatting and displaying output"""
    
    @staticmethod
    def print_success(message: str) -> None:
        """Print a success message"""
        print(f"✅ {message}")
    
    @staticmethod
    def print_error(message: str) -> None:
        """Print an error message"""
        print(f"❌ {message}", file=sys.stderr)
    
    @staticmethod
    def print_warning(message: str) -> None:
        """Print a warning message"""
        print(f"⚠️  {message}")
    
    @staticmethod
    def print_info(message: str) -> None:
        """Print an info message"""
        print(f"ℹ️  {message}")
    
    @staticmethod
    def print_table(headers: List[str], rows: List[List[str]], title: Optional[str] = None) -> None:
        """Print a formatted table"""
        if title:
            print(f"\n{title}")
            print("=" * len(title))
        
        if not rows:
            print("No data to display")
            return
        
        # Calculate column widths
        col_widths = []
        for i, header in enumerate(headers):
            max_width = len(header)
            for row in rows:
                if i < len(row):
                    max_width = max(max_width, len(str(row[i])))
            col_widths.append(max_width)
        
        # Print header
        header_row = " | ".join(header.ljust(width) for header, width in zip(headers, col_widths))
        print(header_row)
        print("-" * len(header_row))
        
        # Print rows
        for row in rows:
            formatted_row = " | ".join(str(cell).ljust(width) for cell, width in zip(row, col_widths))
            print(formatted_row)
    
    @staticmethod
    def print_json(data: Dict[str, Any], indent: int = 2) -> None:
        """Print data as formatted JSON"""
        print(json.dumps(data, indent=indent))
    
    @staticmethod
    def print_progress(current: int, total: int, description: str = "Progress") -> None:
        """Print a progress bar"""
        percentage = (current / total) * 100 if total > 0 else 0
        bar_length = 30
        filled_length = int(bar_length * current // total)
        bar = '█' * filled_length + '-' * (bar_length - filled_length)
        print(f"\r{description}: [{bar}] {percentage:.1f}% ({current}/{total})", end='', flush=True)
        if current == total:
            print()  # New line when complete


class ValidationHelper:
    """Helper for input validation"""
    
    @staticmethod
    def validate_url(url: str) -> bool:
        """Validate if a string is a valid URL"""
        try:
            result = requests.utils.urlparse(url)
            return all([result.scheme, result.netloc])
        except Exception:
            return False
    
    @staticmethod
    def validate_file_path(path: str) -> bool:
        """Validate if a file path exists"""
        return Path(path).exists()
    
    @staticmethod
    def confirm_action(message: str) -> bool:
        """Ask user to confirm an action"""
        response = input(f"{message} (y/N): ").strip().lower()
        return response in ['y', 'yes']
    
    @staticmethod
    def get_input(prompt: str, default: Optional[str] = None, required: bool = True) -> str:
        """Get user input with validation"""
        while True:
            if default:
                user_input = input(f"{prompt} [{default}]: ").strip()
                if not user_input:
                    user_input = default
            else:
                user_input = input(f"{prompt}: ").strip()
            
            if not required or user_input:
                return user_input
            print("This field is required. Please try again.")


# Global instances for easy access
api_client = APIClient()
config_helper = ConfigHelper()
display_helper = DisplayHelper()
validation_helper = ValidationHelper() 