# Sed Compatibility Guide for Cross-Platform Scripts

## The Problem

The `sed` command has different implementations on macOS (BSD sed) and Linux (GNU sed), which can cause scripts to fail when moving between platforms. The most common issue is with in-place editing using the `-i` flag.

## The Issue

**GNU sed (Linux):**
```bash
sed -i 's/old/new/g' file.txt
```

**BSD sed (macOS):**
```bash
sed -i '' 's/old/new/g' file.txt
```

BSD sed requires an extension after `-i`, even if it's empty ('').

## The Solution

### Cross-Platform Syntax

The most reliable cross-platform syntax that works on both macOS and Linux is:

```bash
sed -i'' -e 's/old/new/g' file.txt
```

Note: There's **no space** between `-i` and the empty quotes `''`.

### How We Fixed It

In the conversion script, we changed:
```bash
# Before (only works on Linux)
sed -i "s/CHARTNAME/${CHART_NAME}/g" "charts/hub/${CHART_NAME}/templates/application.yaml"

# After (works on both macOS and Linux)
sed -i'' -e "s/CHARTNAME/${CHART_NAME}/g" "charts/hub/${CHART_NAME}/templates/application.yaml"
```

## Alternative Approaches

### 1. OS Detection Method
```bash
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    sed -i '' 's/old/new/g' file.txt
else
    # Linux
    sed -i 's/old/new/g' file.txt
fi
```

### 2. Using a Backup Extension
```bash
# Works on both, creates .bak file
sed -i.bak 's/old/new/g' file.txt
rm file.txt.bak  # Remove backup if not needed
```

### 3. Using Perl Instead
```bash
# Perl is consistent across platforms
perl -pi -e 's/old/new/g' file.txt
```

### 4. Installing GNU sed on macOS
```bash
brew install gnu-sed
# Then use gsed instead of sed
gsed -i 's/old/new/g' file.txt
```

## Best Practices

1. **For Portability**: Use `sed -i'' -e` syntax
2. **For Clarity**: Add a comment explaining the compatibility
3. **For Testing**: Test scripts on both macOS and Linux
4. **For Documentation**: Document any platform-specific requirements

## Testing the Fix

You can test sed compatibility with:
```bash
# Create test file
echo "CHARTNAME" > test.txt

# Test the command
sed -i'' -e 's/CHARTNAME/myapp/g' test.txt

# Check result
cat test.txt  # Should show: myapp
```

## Common Pitfalls

1. **Space between -i and ''**: Don't add a space
   - ❌ `sed -i '' -e 's/old/new/g'`
   - ✅ `sed -i'' -e 's/old/new/g'`

2. **Forgetting -e**: Always include `-e` with the expression
   - ❌ `sed -i'' 's/old/new/g'`
   - ✅ `sed -i'' -e 's/old/new/g'`

3. **Complex expressions**: For complex sed operations, consider using a sed script file
   ```bash
   sed -i'' -f script.sed file.txt
   ```

## References

- [In-place sed that works on Mac OS and Linux](https://stackoverflow.com/questions/4247068/sed-command-with-i-option-failing-on-mac-but-works-on-linux)
- [Differences between sed on Mac OSX and other "standard" sed](https://unix.stackexchange.com/questions/401905/differences-between-sed-on-mac-osx-and-other-standard-sed)
- [BSD sed vs GNU sed](https://riptutorial.com/sed/topic/9436/bsd-macos-sed-vs--gnu-sed-vs--the-posix-sed-specification)