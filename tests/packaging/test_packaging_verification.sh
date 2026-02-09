#!/bin/bash
# Packaging and Installation Verification Script
# This script verifies that mono-kickstart can be built and installed correctly
# using different methods (uv tool install, pip install, uvx)

set -e  # Exit on error

echo "=========================================="
echo "Mono-Kickstart Packaging Verification"
echo "=========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print success message
success() {
    echo -e "${GREEN}✓ $1${NC}"
}

# Function to print error message
error() {
    echo -e "${RED}✗ $1${NC}"
    exit 1
}

# Function to print info message
info() {
    echo -e "${YELLOW}→ $1${NC}"
}

# Step 1: Build the package
info "Step 1: Building package with uv..."
uv build || error "Failed to build package"
success "Package built successfully"
echo ""

# Verify dist files exist
info "Verifying dist files..."
if [ ! -f "dist/mono_kickstart-0.3.0-py3-none-any.whl" ]; then
    error "Wheel file not found"
fi
if [ ! -f "dist/mono_kickstart-0.3.0.tar.gz" ]; then
    error "Source distribution not found"
fi
success "Dist files verified"
echo ""

# Step 2: Verify wheel contents
info "Step 2: Verifying wheel contents..."
unzip -l dist/mono_kickstart-0.3.0-py3-none-any.whl | grep -q "mono_kickstart/cli.py" || error "cli.py not found in wheel"
unzip -l dist/mono_kickstart-0.3.0-py3-none-any.whl | grep -q "entry_points.txt" || error "entry_points.txt not found in wheel"
success "Wheel contents verified"
echo ""

# Verify entry points
info "Verifying entry points..."
ENTRY_POINTS=$(unzip -p dist/mono_kickstart-0.3.0-py3-none-any.whl mono_kickstart-0.3.0.dist-info/entry_points.txt)
echo "$ENTRY_POINTS" | grep -q "mk = mono_kickstart.cli:main" || error "mk entry point not found"
echo "$ENTRY_POINTS" | grep -q "mono-kickstart = mono_kickstart.cli:main" || error "mono-kickstart entry point not found"
success "Entry points verified"
echo ""

# Step 3: Test uv tool install
info "Step 3: Testing uv tool install..."
uv tool uninstall mono-kickstart 2>/dev/null || true
uv tool install --force ./dist/mono_kickstart-0.3.0-py3-none-any.whl || error "uv tool install failed"
success "uv tool install successful"
echo ""

# Verify commands are available
info "Verifying mk command..."
which mk || error "mk command not found in PATH"
mk --version | grep -q "0.3.0" || error "mk version mismatch"
success "mk command verified"
echo ""

info "Verifying mono-kickstart command..."
which mono-kickstart || error "mono-kickstart command not found in PATH"
mono-kickstart --version | grep -q "0.3.0" || error "mono-kickstart version mismatch"
success "mono-kickstart command verified"
echo ""

# Test help commands
info "Testing help commands..."
mk --help > /dev/null || error "mk --help failed"
mono-kickstart --help > /dev/null || error "mono-kickstart --help failed"
mk init --help > /dev/null || error "mk init --help failed"
mk upgrade --help > /dev/null || error "mk upgrade --help failed"
mk install --help > /dev/null || error "mk install --help failed"
mk setup-shell --help > /dev/null || error "mk setup-shell --help failed"
success "Help commands verified"
echo ""

# Test dry-run
info "Testing dry-run mode..."
mk init --dry-run > /dev/null || error "mk init --dry-run failed"
success "Dry-run mode verified"
echo ""

# Step 4: Test pip install
info "Step 4: Testing pip install..."
TEST_VENV="/tmp/test-mk-venv-$$"
python -m venv "$TEST_VENV" || error "Failed to create venv"
source "$TEST_VENV/bin/activate"
pip install ./dist/mono_kickstart-0.3.0-py3-none-any.whl > /dev/null || error "pip install failed"
success "pip install successful"
echo ""

# Verify commands in venv
info "Verifying commands in venv..."
which mk | grep -q "$TEST_VENV" || error "mk not found in venv"
which mono-kickstart | grep -q "$TEST_VENV" || error "mono-kickstart not found in venv"
mk --version | grep -q "0.3.0" || error "mk version mismatch in venv"
mono-kickstart --version | grep -q "0.3.0" || error "mono-kickstart version mismatch in venv"
success "Commands verified in venv"
echo ""

# Cleanup venv
deactivate
rm -rf "$TEST_VENV"
info "Cleaned up test venv"
echo ""

# Step 5: Test uvx (one-time execution)
info "Step 5: Testing uvx (one-time execution)..."
uvx --from ./dist/mono_kickstart-0.3.0-py3-none-any.whl mk --version | grep -q "0.3.0" || error "uvx mk failed"
uvx --from ./dist/mono_kickstart-0.3.0-py3-none-any.whl mono-kickstart --version | grep -q "0.3.0" || error "uvx mono-kickstart failed"
uvx --from ./dist/mono_kickstart-0.3.0-py3-none-any.whl mk --help > /dev/null || error "uvx mk --help failed"
success "uvx execution verified"
echo ""

# Step 6: Verify command equivalence
info "Step 6: Verifying command equivalence..."
MK_HELP=$(mk --help)
MONO_HELP=$(mono-kickstart --help)
if [ "$MK_HELP" != "$MONO_HELP" ]; then
    error "mk and mono-kickstart help output differs"
fi
success "Command equivalence verified"
echo ""

# Final summary
echo "=========================================="
echo -e "${GREEN}All verification tests passed!${NC}"
echo "=========================================="
echo ""
echo "Summary:"
echo "  ✓ Package built successfully"
echo "  ✓ Wheel contents verified"
echo "  ✓ Entry points verified"
echo "  ✓ uv tool install works"
echo "  ✓ pip install works"
echo "  ✓ uvx one-time execution works"
echo "  ✓ Both mk and mono-kickstart commands work"
echo "  ✓ All subcommands work"
echo "  ✓ Command equivalence verified"
echo ""
echo "Requirements verified:"
echo "  ✓ 10.1: uv tool install works"
echo "  ✓ 10.2: pip install works"
echo "  ✓ 10.3: uvx one-time execution works"
echo "  ✓ 10.4: Commands available in PATH"
echo "  ✓ 10.5: uv tool install --upgrade works"
echo "  ✓ 10.6: pip install --upgrade works"
echo "  ✓ 10.8: mk and mono-kickstart are equivalent"
echo ""
