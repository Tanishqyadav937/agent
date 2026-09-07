#!/bin/bash

# Quick rigging helper script

echo "=========================================="
echo "Bunny Rigging - Quick Start"
echo "=========================================="
echo ""

# Check files exist
if [ ! -f "/Users/tanishqyadav/agent/bunny_character_fixed_tail.glb" ]; then
  echo "❌ Error: Fixed tail model not found!"
  echo "   Run: blender --background --python blender_fix_tail.py"
  exit 1
fi

echo "✅ Fixed tail model found"
echo ""

echo "Opening Blender with fixed bunny model..."
echo ""
echo "Manual Steps Required:"
echo "  1. Create armature (Shift+A → Armature)"
echo "  2. Edit bones in Edit Mode (Tab)"
echo "  3. Parent mesh to armature:"
echo "     - Select mesh"
echo "     - Shift+select armature"
echo "     - Ctrl+P → 'With Automatic Weights'"
echo "  4. Test pose (Ctrl+Tab → Pose Mode)"
echo "  5. Export: File → Export → glTF 2.0 (.glb)"
echo "     - Check 'Skinning' option"
echo "     - Save as: bunny_rigged.glb"
echo ""
echo "See BUNNY_RIGGING_GUIDE.md for detailed instructions."
echo ""
echo "Press Enter to open Blender..."
read

/opt/homebrew/bin/blender /Users/tanishqyadav/agent/bunny_character_fixed_tail.glb
