#!/usr/bin/env python3
"""
Create presentation from markdown
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def create_text_presentation(md_file: Path, output_file: Path):
    """Convert markdown presentation to text format"""
    
    with open(md_file, 'r') as f:
        content = f.read()
    
    slides = content.split('---\n')
    
    output = []
    output.append("=" * 70)
    output.append("TALENTMIND AI - INVESTOR PRESENTATION")
    output.append("=" * 70)
    output.append("")
    
    for i, slide in enumerate(slides, 1):
        lines = slide.strip().split('\n')
        
        output.append(f"\n{'=' * 70}")
        output.append(f"SLIDE {i}")
        output.append("=" * 70)
        output.append("")
        
        for line in lines:
            if line.startswith('##'):
                output.append(f"\n{line[2:].upper()}")
                output.append("-" * len(line[2:]))
            elif line.startswith('#'):
                output.append(f"\n{line[1:].upper()}")
                output.append("=" * len(line[1:]))
            elif line.strip():
                output.append(line)
        
        output.append("")
    
    with open(output_file, 'w') as f:
        f.write('\n'.join(output))
    
    print(f"Text presentation saved to {output_file}")

if __name__ == "__main__":
    md_file = Path(__file__).parent.parent / "docs" / "PRESENTATION.md"
    output_file = Path(__file__).parent.parent / "outputs" / "PRESENTATION.txt"
    
    create_text_presentation(md_file, output_file)