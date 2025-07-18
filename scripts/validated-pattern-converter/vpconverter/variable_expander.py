"""
Variable expansion engine for GNU Make variables.

This module handles proper variable expansion in Makefiles including:
- $(VAR) and ${VAR} patterns
- Automatic variables ($@, $<, $^, etc.)
- Function calls ($(shell), $(wildcard), etc.)
- Recursive and simple expansion
"""

import re
import os
from pathlib import Path
from typing import Dict, List, Optional, Set, Any
from dataclasses import dataclass, field

from .utils import log_info, log_warn


@dataclass
class VariableExpansion:
    """Results of variable expansion."""
    original: str
    expanded: str
    variables_used: Set[str] = field(default_factory=set)
    functions_used: Set[str] = field(default_factory=set)
    automatic_vars_used: Set[str] = field(default_factory=set)
    unexpanded_vars: Set[str] = field(default_factory=set)


class VariableExpander:
    """Handles GNU Make variable expansion."""
    
    # Automatic variables that GNU Make provides
    AUTOMATIC_VARIABLES = {
        '$@': 'target_name',           # The target name
        '$<': 'first_prerequisite',    # First prerequisite
        '$^': 'all_prerequisites',     # All prerequisites
        '$?': 'newer_prerequisites',   # Prerequisites newer than target
        '$*': 'stem',                  # The stem of pattern rules
        '$+': 'all_prerequisites_dup', # All prerequisites with duplicates
        '$|': 'order_only_prereqs',    # Order-only prerequisites
        '$%': 'target_member',         # Target member name (archives)
        '$(@D)': 'target_dir',         # Directory of target
        '$(@F)': 'target_file',        # File part of target
        '$(<D)': 'first_prereq_dir',   # Directory of first prerequisite
        '$(<F)': 'first_prereq_file',  # File part of first prerequisite
        '$(^D)': 'all_prereq_dirs',    # Directories of all prerequisites
        '$(^F)': 'all_prereq_files',   # File parts of all prerequisites
        '$(?D)': 'newer_prereq_dirs',  # Directories of newer prerequisites
        '$(?F)': 'newer_prereq_files', # File parts of newer prerequisites
        '$(*D)': 'stem_dir',           # Directory of stem
        '$(*F)': 'stem_file',          # File part of stem
    }
    
    # Function patterns that GNU Make supports
    FUNCTION_PATTERNS = {
        'shell': r'\$\(shell\s+([^)]+)\)',
        'wildcard': r'\$\(wildcard\s+([^)]+)\)',
        'foreach': r'\$\(foreach\s+([^,]+),\s*([^,]+),\s*([^)]+)\)',
        'if': r'\$\(if\s+([^,]+),\s*([^,]*),\s*([^)]*)\)',
        'or': r'\$\(or\s+([^)]+)\)',
        'and': r'\$\(and\s+([^)]+)\)',
        'strip': r'\$\(strip\s+([^)]+)\)',
        'findstring': r'\$\(findstring\s+([^,]+),\s*([^)]+)\)',
        'filter': r'\$\(filter\s+([^,]+),\s*([^)]+)\)',
        'filter-out': r'\$\(filter-out\s+([^,]+),\s*([^)]+)\)',
        'sort': r'\$\(sort\s+([^)]+)\)',
        'word': r'\$\(word\s+([^,]+),\s*([^)]+)\)',
        'wordlist': r'\$\(wordlist\s+([^,]+),\s*([^,]+),\s*([^)]+)\)',
        'words': r'\$\(words\s+([^)]+)\)',
        'firstword': r'\$\(firstword\s+([^)]+)\)',
        'lastword': r'\$\(lastword\s+([^)]+)\)',
        'dir': r'\$\(dir\s+([^)]+)\)',
        'notdir': r'\$\(notdir\s+([^)]+)\)',
        'suffix': r'\$\(suffix\s+([^)]+)\)',
        'basename': r'\$\(basename\s+([^)]+)\)',
        'addsuffix': r'\$\(addsuffix\s+([^,]+),\s*([^)]+)\)',
        'addprefix': r'\$\(addprefix\s+([^,]+),\s*([^)]+)\)',
        'join': r'\$\(join\s+([^,]+),\s*([^)]+)\)',
        'subst': r'\$\(subst\s+([^,]+),\s*([^,]+),\s*([^)]+)\)',
        'patsubst': r'\$\(patsubst\s+([^,]+),\s*([^,]+),\s*([^)]+)\)',
        'call': r'\$\(call\s+([^,]+)(?:,\s*([^)]*))?\)',
        'value': r'\$\(value\s+([^)]+)\)',
        'eval': r'\$\(eval\s+([^)]+)\)',
        'origin': r'\$\(origin\s+([^)]+)\)',
        'flavor': r'\$\(flavor\s+([^)]+)\)',
        'error': r'\$\(error\s+([^)]+)\)',
        'warning': r'\$\(warning\s+([^)]+)\)',
        'info': r'\$\(info\s+([^)]+)\)',
        'abspath': r'\$\(abspath\s+([^)]+)\)',
        'realpath': r'\$\(realpath\s+([^)]+)\)',
    }
    
    def __init__(self, variables: Dict[str, str], environment: Dict[str, str] = None, base_path: Path = None):
        """Initialize variable expander.
        
        Args:
            variables: Make variables defined in the Makefile
            environment: Environment variables
            base_path: Base path for relative path resolution
        """
        self.variables = variables.copy()
        self.environment = environment or dict(os.environ)
        self.base_path = base_path or Path.cwd()
        self.expansion_cache: Dict[str, VariableExpansion] = {}
        self.recursion_stack: Set[str] = set()
        self.max_recursion_depth = 50
        
        # Apply default values for conditional variables not explicitly set
        self._apply_conditional_defaults()
        
        # Compile function patterns
        self.function_regexes = {
            name: re.compile(pattern, re.IGNORECASE)
            for name, pattern in self.FUNCTION_PATTERNS.items()
        }
        
        # Compile variable patterns
        self.var_pattern = re.compile(r'\$\(([^)]+)\)|\$\{([^}]+)\}|\$([a-zA-Z_][a-zA-Z0-9_]*|\$|[@<^?*+|%])')
    
    def _apply_conditional_defaults(self):
        """Apply default values for variables that have ?= assignments."""
        # Common defaults for variables that might be defined with ?= after being referenced
        defaults = {
            'METRIC_UI_CHART_PATH': 'metric-ui',
            'PROMETHEUS_CHART_PATH': 'prometheus',
            'METRIC_UI_RELEASE_NAME': 'metric-ui',
            'PROMETHEUS_RELEASE_NAME': 'prometheus',
            'REGION': 'us-east-1'
        }
        
        for var_name, default_value in defaults.items():
            if var_name not in self.variables:
                self.variables[var_name] = default_value
    
    def expand(self, text: str, target_name: str = None, dependencies: List[str] = None) -> VariableExpansion:
        """Expand variables in text.
        
        Args:
            text: Text to expand
            target_name: Current target name for automatic variables
            dependencies: Target dependencies for automatic variables
            
        Returns:
            VariableExpansion object with results
        """
        cache_key = f"{text}:{target_name}:{':'.join(dependencies or [])}"
        
        if cache_key in self.expansion_cache:
            return self.expansion_cache[cache_key]
        
        if len(self.recursion_stack) > self.max_recursion_depth:
            log_warn(f"Maximum recursion depth reached expanding: {text}")
            return VariableExpansion(
                original=text,
                expanded=text,
                unexpanded_vars={text}
            )
        
        result = VariableExpansion(original=text, expanded=text)
        
        # Handle automatic variables first
        if target_name:
            result.expanded = self._expand_automatic_variables(
                result.expanded, target_name, dependencies or [], result
            )
        
        # Handle function calls
        result.expanded = self._expand_function_calls(result.expanded, result)
        
        # Handle variable references
        result.expanded = self._expand_variable_references(result.expanded, result)
        
        self.expansion_cache[cache_key] = result
        return result
    
    def _expand_automatic_variables(self, text: str, target_name: str, dependencies: List[str], result: VariableExpansion) -> str:
        """Expand automatic variables like $@, $<, $^, etc."""
        expansions = {
            '$@': target_name,
            '$<': dependencies[0] if dependencies else '',
            '$^': ' '.join(dependencies),
            '$?': ' '.join(dependencies),  # Simplified - would need timestamp comparison
            '$*': self._get_stem(target_name),
            '$+': ' '.join(dependencies),  # Same as $^ for simplicity
            '$|': '',  # Order-only prerequisites - would need parsing
            '$%': '',  # Archive member - rarely used
        }
        
        # Add directory and file variants
        if target_name:
            target_path = Path(target_name)
            expansions.update({
                '$(@D)': str(target_path.parent) if target_path.parent != Path('.') else '.',
                '$(@F)': target_path.name,
            })
        
        if dependencies:
            first_dep = Path(dependencies[0])
            expansions.update({
                '$(<D)': str(first_dep.parent) if first_dep.parent != Path('.') else '.',
                '$(<F)': first_dep.name,
            })
        
        for var, value in expansions.items():
            if var in text:
                text = text.replace(var, value)
                result.automatic_vars_used.add(var)
        
        return text
    
    def _expand_function_calls(self, text: str, result: VariableExpansion) -> str:
        """Expand function calls like $(shell command)."""
        for func_name, regex in self.function_regexes.items():
            matches = list(regex.finditer(text))
            
            for match in reversed(matches):  # Process from end to avoid offset issues
                result.functions_used.add(func_name)
                # Filter out None values from match groups
                groups = tuple(group if group is not None else '' for group in match.groups())
                replacement = self._evaluate_function(func_name, groups)
                text = text[:match.start()] + replacement + text[match.end():]
        
        return text
    
    def _expand_variable_references(self, text: str, result: VariableExpansion) -> str:
        """Expand variable references like $(VAR) and ${VAR}."""
        matches = list(self.var_pattern.finditer(text))
        
        for match in reversed(matches):  # Process from end to avoid offset issues
            var_name = match.group(1) or match.group(2) or match.group(3)
            
            if not var_name:
                continue
            
            # Skip if it's an automatic variable (already handled)
            if match.group(0) in self.AUTOMATIC_VARIABLES:
                continue
            
            # Get variable value
            value = self._get_variable_value(var_name, result)
            
            # Replace in text
            text = text[:match.start()] + value + text[match.end():]
        
        return text
    
    def _get_variable_value(self, var_name: str, result: VariableExpansion) -> str:
        """Get variable value with proper precedence and recursion handling."""
        # Handle special case of literal $ character
        if var_name == '$':
            # Don't treat as unexpanded - it's a literal $
            return '$'
        
        # Check recursion
        if var_name in self.recursion_stack:
            log_warn(f"Circular reference detected for variable: {var_name}")
            result.unexpanded_vars.add(var_name)
            return f"${{{var_name}}}"
        
        # Mark as used
        result.variables_used.add(var_name)
        
        # Check Make variables first
        if var_name in self.variables:
            self.recursion_stack.add(var_name)
            try:
                value = self.variables[var_name]
                # Recursively expand the value
                if '$' in value:
                    expanded = self.expand(value)
                    value = expanded.expanded
                    result.variables_used.update(expanded.variables_used)
                    result.functions_used.update(expanded.functions_used)
                    result.automatic_vars_used.update(expanded.automatic_vars_used)
                    result.unexpanded_vars.update(expanded.unexpanded_vars)
                return value
            finally:
                self.recursion_stack.remove(var_name)
        
        # Check environment variables
        elif var_name in self.environment:
            return self.environment[var_name]
        
        # Check special variables
        elif var_name == 'MAKE':
            return 'make'
        elif var_name == 'MAKEFILE_LIST':
            return 'Makefile'
        elif var_name == 'CURDIR':
            return str(self.base_path)
        elif var_name == '.DEFAULT_GOAL':
            return 'default'
        
        # Handle common conditional variables that are intentionally undefined
        elif var_name in ['LLM', 'SAFETY', 'SAFETY_TOLERATION', 'LLM_TOLERATION', 'EXTRA_HELM_ARGS']:
            # These are meant to be undefined by default - don't expand them
            return f"${{{var_name}}}"
        
        # Variable not found
        else:
            result.unexpanded_vars.add(var_name)
            return f"${{{var_name}}}"
    
    def _safe_args_string(self, args: tuple) -> str:
        """Create a safe string representation of function arguments."""
        safe_args = [str(arg) if arg is not None else '' for arg in args]
        return ':'.join(safe_args)
    
    def _evaluate_function(self, func_name: str, args: tuple) -> str:
        """Evaluate a function call."""
        # For security and simplicity, we'll return placeholders for most functions
        # In a full implementation, these would be properly evaluated
        
        # Handle None values in args
        args = tuple(arg if arg is not None else '' for arg in args)
        
        if func_name == 'shell':
            command = args[0] if args else ''
            return f"<shell:{command.strip()}>"
        
        elif func_name == 'wildcard':
            pattern = args[0] if args else ''
            try:
                # Actually expand wildcards for better analysis
                from glob import glob
                files = glob(pattern.strip())
                return ' '.join(files)
            except Exception:
                return f"<wildcard:{pattern.strip()}>"
        
        elif func_name == 'dir':
            path = args[0] if args else ''
            try:
                return str(Path(path.strip()).parent) + '/'
            except Exception:
                return f"<dir:{path.strip()}>"
        
        elif func_name == 'notdir':
            path = args[0] if args else ''
            try:
                return Path(path.strip()).name
            except Exception:
                return f"<notdir:{path.strip()}>"
        
        elif func_name == 'basename':
            path = args[0] if args else ''
            try:
                return Path(path.strip()).stem
            except Exception:
                return f"<basename:{path.strip()}>"
        
        elif func_name == 'suffix':
            path = args[0] if args else ''
            try:
                return Path(path.strip()).suffix
            except Exception:
                return f"<suffix:{path.strip()}>"
        
        elif func_name == 'abspath':
            path = args[0] if args else ''
            try:
                return str(Path(path.strip()).resolve())
            except Exception:
                return f"<abspath:{path.strip()}>"
        
        elif func_name == 'strip':
            text = args[0] if args else ''
            return text.strip()
        
        elif func_name == 'subst':
            if len(args) >= 3:
                from_text, to_text, text = args[0], args[1], args[2]
                return text.replace(from_text, to_text)
            return f"<subst:{self._safe_args_string(args)}>"
        
        elif func_name == 'patsubst':
            if len(args) >= 3:
                pattern, replacement, text = args[0], args[1], args[2]
                # Simplified pattern substitution
                if '%' in pattern:
                    # Convert Make pattern to regex
                    regex_pattern = pattern.replace('%', '(.*)')
                    regex_replacement = replacement.replace('%', r'\1')
                    import re
                    return re.sub(regex_pattern, regex_replacement, text)
                return text.replace(pattern, replacement)
            return f"<patsubst:{self._safe_args_string(args)}>"
        
        elif func_name == 'sort':
            text = args[0] if args else ''
            words = text.split()
            return ' '.join(sorted(set(words)))
        
        elif func_name == 'words':
            text = args[0] if args else ''
            return str(len(text.split()))
        
        elif func_name == 'firstword':
            text = args[0] if args else ''
            words = text.split()
            return words[0] if words else ''
        
        elif func_name == 'lastword':
            text = args[0] if args else ''
            words = text.split()
            return words[-1] if words else ''
        
        elif func_name == 'if':
            condition = args[0] if len(args) > 0 else ''
            then_part = args[1] if len(args) > 1 else ''
            else_part = args[2] if len(args) > 2 else ''
            # Simple condition evaluation
            return then_part if condition.strip() else else_part
        
        else:
            # For other functions, return a placeholder
            return f"<{func_name}:{self._safe_args_string(args)}>"
    
    def _get_stem(self, target_name: str) -> str:
        """Get the stem for pattern rules."""
        # This would be more complex in a full implementation
        # For now, return the basename without extension
        return Path(target_name).stem
    
    def expand_all_targets(self, targets: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """Expand variables in all target commands.
        
        Args:
            targets: Dictionary of target objects with commands
            
        Returns:
            Dictionary mapping target names to expansion results
        """
        results = {}
        
        for target_name, target in targets.items():
            target_results = {
                'commands': [],
                'dependencies': [],
                'variables_used': set(),
                'functions_used': set(),
                'automatic_vars_used': set(),
                'unexpanded_vars': set()
            }
            
            # Expand dependencies
            for dep in getattr(target, 'dependencies', []):
                expanded = self.expand(dep, target_name)
                target_results['dependencies'].append(expanded.expanded)
                target_results['variables_used'].update(expanded.variables_used)
                target_results['functions_used'].update(expanded.functions_used)
                target_results['automatic_vars_used'].update(expanded.automatic_vars_used)
                target_results['unexpanded_vars'].update(expanded.unexpanded_vars)
            
            # Expand commands
            for command in getattr(target, 'commands', []):
                expanded = self.expand(command, target_name, target_results['dependencies'])
                target_results['commands'].append({
                    'original': command,
                    'expanded': expanded.expanded,
                    'variables_used': expanded.variables_used,
                    'functions_used': expanded.functions_used,
                    'automatic_vars_used': expanded.automatic_vars_used,
                    'unexpanded_vars': expanded.unexpanded_vars
                })
                target_results['variables_used'].update(expanded.variables_used)
                target_results['functions_used'].update(expanded.functions_used)
                target_results['automatic_vars_used'].update(expanded.automatic_vars_used)
                target_results['unexpanded_vars'].update(expanded.unexpanded_vars)
            
            results[target_name] = target_results
        
        return results
    
    def get_expansion_summary(self) -> Dict[str, Any]:
        """Get summary of all expansions performed."""
        all_variables = set()
        all_functions = set()
        all_automatic = set()
        all_unexpanded = set()
        
        for expansion in self.expansion_cache.values():
            all_variables.update(expansion.variables_used)
            all_functions.update(expansion.functions_used)
            all_automatic.update(expansion.automatic_vars_used)
            all_unexpanded.update(expansion.unexpanded_vars)
        
        return {
            'total_expansions': len(self.expansion_cache),
            'variables_used': sorted(all_variables),
            'functions_used': sorted(all_functions),
            'automatic_vars_used': sorted(all_automatic),
            'unexpanded_vars': sorted(all_unexpanded),
            'defined_variables': sorted(self.variables.keys()),
            'available_env_vars': len(self.environment)
        }