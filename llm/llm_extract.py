"""
LLM-based member extraction using Groq's Llama 4 Maverick.

Provides more accurate extraction than OCR by understanding game UI context.
"""

import base64
import json
import os
from pathlib import Path

from groq import Groq

# Load .env file if present
env_path = Path(__file__).parent.parent / ".env"
if env_path.exists():
    with open(env_path) as f:
        for line in f:
            if "=" in line and not line.startswith("#"):
                key, val = line.strip().split("=", 1)
                os.environ.setdefault(key, val)

# Groq API configuration
API_KEY = os.environ.get("GROQ_API_KEY")
MODEL = "meta-llama/llama-4-maverick-17b-128e-instruct"

if not API_KEY:
    raise ValueError("GROQ_API_KEY not set. Create .env file or run: export GROQ_API_KEY='your_key'")


def encode_image(image_path: str) -> str:
    """Encode image to base64 for Groq API."""
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def extract_members(image_path: str) -> list[dict]:
    """
    Extract member data from a screenshot using Llama 4 Maverick.
    
    Args:
        image_path: Path to the screenshot PNG file
        
    Returns:
        List of dicts with keys: name, ovr, activity
    """
    client = Groq(api_key=API_KEY)
    
    # Encode image to base64
    image_data = encode_image(image_path)
    
    # Craft prompt for structured extraction
    prompt = """Analyze this FC Mobile league member list screenshot.

Extract ALL visible player entries from the MEMBERS list on the right side.

For EACH player, extract:
1. name: The player's username (e.g., "AxeKing", "TREK", "Dark")
2. ovr: Their OVR rating number shown below the name (e.g., 125)
3. activity: Their activity score on the right (e.g., 5115, 6245)

Return ONLY a valid JSON array with objects containing these 3 fields.
Example format:
[
  {"name": "AxeKing", "ovr": 125, "activity": 5115},
  {"name": "TREK", "ovr": 125, "activity": 6245}
]

If you cannot determine a value, use 0 for numbers.
Return ONLY the JSON array, no other text."""

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{image_data}"
                            }
                        }
                    ]
                }
            ],
            temperature=0.1,  # Low temperature for consistent extraction
            max_tokens=2000
        )
        
        # Parse response
        content = response.choices[0].message.content.strip()
        
        # Extract JSON from response (handle markdown code blocks)
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()
        
        members = json.loads(content)
        return members
        
    except json.JSONDecodeError as e:
        print(f"  JSON parse error: {e}")
        print(f"  Raw response: {content[:200]}...")
        return []
    except Exception as e:
        print(f"  API error: {e}")
        return []


def test_single():
    """Test extraction on a single screenshot."""
    test_image = "screenshots/ss_00.png"
    
    if not os.path.exists(test_image):
        print(f"Test image not found: {test_image}")
        return
    
    print(f"Testing extraction on {test_image}...")
    print("-" * 60)
    
    members = extract_members(test_image)
    
    print(f"\nExtracted {len(members)} members:")
    print("-" * 60)
    
    for m in members:
        print(f"  {m.get('name', '?'):20} OVR:{m.get('ovr', 0):3}  Activity:{m.get('activity', 0)}")
    
    print("-" * 60)
    print(json.dumps(members, indent=2))


if __name__ == "__main__":
    test_single()
