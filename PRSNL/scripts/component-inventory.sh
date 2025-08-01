#!/bin/bash

# Component Inventory Script for PRSNL
# Helps prevent duplication in 118+ components

echo "🧩 PRSNL Component Inventory Analysis"
echo "====================================="
echo ""

# Count total components
TOTAL_COMPONENTS=$(find ../frontend/src/lib/components -name "*.svelte" | wc -l)
echo "📊 Total Svelte Components: $TOTAL_COMPONENTS"
echo ""

# List components by category
echo "📁 Components by Category:"
echo "--------------------------"

# UI Components
echo ""
echo "🎨 UI Components:"
find ../frontend/src/lib/components -name "*.svelte" | grep -E "(Button|Modal|Card|Input|Form|Table)" | sort

# Layout Components
echo ""
echo "📐 Layout Components:"
find ../frontend/src/lib/components -name "*.svelte" | grep -E "(Layout|Header|Footer|Sidebar|Nav)" | sort

# Data Display Components
echo ""
echo "📊 Data Display Components:"
find ../frontend/src/lib/components -name "*.svelte" | grep -E "(List|Grid|Chart|Graph|Visualization)" | sort

# Media Components
echo ""
echo "🎬 Media Components:"
find ../frontend/src/lib/components -name "*.svelte" | grep -E "(Video|Image|Audio|Media|Player)" | sort

# State Components
echo ""
echo "🔄 State Components:"
find ../frontend/src/lib/components -name "*.svelte" | grep -E "(Loading|Error|Empty|Spinner)" | sort

# Store component patterns in Cipher
echo ""
echo "💾 Storing component inventory in Cipher..."

# Common UI patterns
./prsnl-cipher.sh store "COMPONENT INVENTORY: Loading states → Spinner.svelte, LoadingOverlay.svelte, SkeletonLoader.svelte"
./prsnl-cipher.sh store "COMPONENT INVENTORY: Modals → Modal.svelte, ConfirmDialog.svelte, ModalWrapper.svelte"
./prsnl-cipher.sh store "COMPONENT INVENTORY: Forms → DynamicInput.svelte, FormField.svelte, ValidationError.svelte"
./prsnl-cipher.sh store "COMPONENT INVENTORY: Tables → DataTable.svelte, TableHeader.svelte, TablePagination.svelte"
./prsnl-cipher.sh store "COMPONENT INVENTORY: Empty states → EmptyState.svelte, NoResults.svelte, ZeroState.svelte"

# Search function
echo ""
echo "🔍 Component Search Function:"
echo "-----------------------------"
echo "To search for existing components before creating new ones:"
echo ""
echo "  # Search by name:"
echo "  grep -r --include="*.svelte" 'Button' ../frontend/src/lib/components/"
echo ""
echo "  # Search by functionality:"
echo "  grep -r --include="*.svelte" 'upload\\|Upload' ../frontend/src/lib/components/"
echo ""
echo "  # Search by props:"
echo "  grep -r --include="*.svelte" 'export let.*loading' ../frontend/src/lib/components/"
echo ""

# Duplication check
echo "🔍 Checking for potential duplicates..."
echo "--------------------------------------"

# Find similar component names
echo ""
echo "⚠️  Potential duplicate patterns:"
find ../frontend/src/lib/components -name "*.svelte" | sed 's/.*\///' | sort | uniq -d

# Components with similar purposes
echo ""
echo "📝 Components to review for consolidation:"
echo "  - Loading components: $(find frontend/src/lib/components -name "*Load*.svelte" -o -name "*Spinner*.svelte" | wc -l) files"
echo "  - Modal components: $(find frontend/src/lib/components -name "*Modal*.svelte" -o -name "*Dialog*.svelte" | wc -l) files"
echo "  - Button components: $(find frontend/src/lib/components -name "*Button*.svelte" -o -name "*Btn*.svelte" | wc -l) files"
echo "  - Input components: $(find frontend/src/lib/components -name "*Input*.svelte" -o -name "*Field*.svelte" | wc -l) files"

# Generate component usage report
echo ""
echo "📈 Generating component usage patterns..."
echo "----------------------------------------"

# Store search patterns for common needs
./prsnl-cipher.sh store "BEFORE CREATING: Search 'grep -r --include="*.svelte" Modal ../frontend/src/lib/components/' for modal dialogs"
./prsnl-cipher.sh store "BEFORE CREATING: Search 'grep -r --include="*.svelte" Loading ../frontend/src/lib/components/' for loading states"
./prsnl-cipher.sh store "BEFORE CREATING: Search 'grep -r --include="*.svelte" Table ../frontend/src/lib/components/' for data tables"
./prsnl-cipher.sh store "BEFORE CREATING: Search 'grep -r --include="*.svelte" Upload ../frontend/src/lib/components/' for file uploads"
./prsnl-cipher.sh store "BEFORE CREATING: Search 'grep -r --include="*.svelte" Error ../frontend/src/lib/components/' for error displays"

echo ""
echo "✅ Component inventory analysis complete!"
echo ""
echo "💡 Next steps:"
echo "  1. Review potential duplicates listed above"
echo "  2. Use search commands before creating new components"
echo "  3. Store successful component reuse in Cipher"
echo "  4. Run this script weekly to track component growth"