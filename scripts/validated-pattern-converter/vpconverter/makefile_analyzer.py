"""
Makefile analyzer for validated pattern converter.

This module analyzes Makefiles found in Helm directories to understand
the deployment process and generate flow diagrams.
"""

import re
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Any
from dataclasses import dataclass, field

from .utils import log_info, log_warn, console

# Import variable expander
try:
    from .variable_expander import VariableExpander
    VARIABLE_EXPANSION_AVAILABLE = True
except ImportError:
    VARIABLE_EXPANSION_AVAILABLE = False


@dataclass
class MakefileTarget:
    """Represents a Makefile target with its dependencies and commands."""
    name: str
    dependencies: List[str] = field(default_factory=list)
    commands: List[str] = field(default_factory=list)
    description: Optional[str] = None
    is_phony: bool = False
    is_pattern_rule: bool = False
    is_double_colon: bool = False
    calls_scripts: List[str] = field(default_factory=list)
    uses_helm: bool = False
    uses_kubectl: bool = False
    uses_oc: bool = False


@dataclass
class MakefileAnalysis:
    """Results from Makefile analysis."""
    path: Path
    targets: Dict[str, MakefileTarget] = field(default_factory=dict)
    pattern_rules: List[MakefileTarget] = field(default_factory=list)
    variables: Dict[str, str] = field(default_factory=dict)
    includes: List[str] = field(default_factory=list)
    has_install_target: bool = False
    has_uninstall_target: bool = False
    install_flow: List[str] = field(default_factory=list)
    uninstall_flow: List[str] = field(default_factory=list)
    detected_tools: Set[str] = field(default_factory=set)
    # Variable expansion results
    variable_expansion_results: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    expansion_summary: Dict[str, Any] = field(default_factory=dict)


class MakefileAnalyzer:
    """Analyzes Makefiles to understand deployment processes.

    Based on GNU Make specification: https://www.gnu.org/software/make/manual/make.html
    """

    # Common deployment-related target names
    INSTALL_KEYWORDS = ['install', 'deploy', 'apply', 'setup', 'bootstrap', 'init']
    UNINSTALL_KEYWORDS = ['uninstall', 'undeploy', 'remove', 'cleanup', 'destroy', 'delete']

    # Common tool patterns
    TOOL_PATTERNS = {
        'helm': re.compile(r'\b(helm)\s+(install|upgrade|delete|uninstall|template)', re.IGNORECASE),
        'kubectl': re.compile(r'\b(kubectl)\s+(apply|create|delete|patch)', re.IGNORECASE),
        'oc': re.compile(r'\b(oc)\s+(apply|create|delete|new-app|process)', re.IGNORECASE),
        'kustomize': re.compile(r'\b(kustomize)\s+(build|edit)', re.IGNORECASE),
        'argocd': re.compile(r'\b(argocd)\s+(app|repo|cluster)', re.IGNORECASE),
        'ansible': re.compile(r'\b(ansible-playbook|ansible)', re.IGNORECASE),
        'make': re.compile(r'\b(make)\s+(-C\s+)?(\S+)', re.IGNORECASE),
    }

    # Script call patterns
    SCRIPT_PATTERNS = [
        re.compile(r'\./([\w\-\.]+\.sh)'),  # ./script.sh
        re.compile(r'bash\s+([\w\-\.\/]+\.sh)'),  # bash script.sh
        re.compile(r'sh\s+([\w\-\.\/]+\.sh)'),  # sh script.sh
        re.compile(r'\$\(?(PWD|ROOT_DIR|SCRIPT_DIR)[^\)]*\)?\/([\w\-\.\/]+\.sh)'),  # $(PWD)/script.sh
    ]

    # Special targets that GNU Make recognizes
    SPECIAL_TARGETS = ['.PHONY', '.SUFFIXES', '.DEFAULT', '.PRECIOUS', '.INTERMEDIATE',
                      '.SECONDARY', '.SECONDEXPANSION', '.DELETE_ON_ERROR', '.IGNORE',
                      '.LOW_RESOLUTION_TIME', '.SILENT', '.EXPORT_ALL_VARIABLES',
                      '.NOTPARALLEL', '.ONESHELL', '.POSIX']

    def __init__(self, makefile_path: Path):
        """Initialize analyzer with Makefile path."""
        self.makefile_path = makefile_path
        self.makefile_dir = makefile_path.parent
        self.analysis = MakefileAnalysis(path=makefile_path)
        self._in_define = False
        self._define_var = None
        self._conditional_stack = []

    def analyze(self, verbose: bool = False) -> MakefileAnalysis:
        """Analyze the Makefile and trace through dependencies."""
        log_info(f"Analyzing Makefile: {self.makefile_path}")

        # Parse the Makefile
        self._parse_makefile()

        # Detect deployment tools
        self._detect_tools()

        # Find install/uninstall targets
        self._identify_deployment_targets()

        # Trace install/uninstall flows
        if self.analysis.has_install_target:
            self._trace_target_flow('install')

        if self.analysis.has_uninstall_target:
            self._trace_target_flow('uninstall')

        # Analyze called scripts
        if verbose:
            self._analyze_called_scripts()

        # Perform variable expansion analysis
        self._analyze_variable_expansion(verbose)

        return self.analysis

    def _parse_makefile(self) -> None:
        """Parse Makefile content into targets, variables, and includes.

        Handles GNU Make features including:
        - Line continuations with backslash
        - Pattern rules (%.o: %.c)
        - Double-colon rules (target::)
        - Conditional directives (ifeq, ifdef, etc.)
        - Multi-line variable definitions (define...endef)
        - Include directives
        """
        with open(self.makefile_path, 'r') as f:
            lines = f.readlines()

        current_target = None
        in_recipe = False
        continued_line = ""
        i = 0

        while i < len(lines):
            # Handle line continuations
            line = lines[i].rstrip('\n')

            # Accumulate continued lines
            while line.endswith('\\') and i + 1 < len(lines):
                continued_line += line[:-1] + ' '
                i += 1
                line = lines[i].rstrip('\n')

            # Add the final line (or the only line if no continuation)
            full_line = continued_line + line
            continued_line = ""

            # Skip empty lines
            if not full_line.strip():
                i += 1
                continue

            # Handle multi-line variable definitions (define...endef)
            if full_line.strip().startswith('define '):
                self._define_var = full_line.strip().split()[1]
                self._in_define = True
                self.analysis.variables[self._define_var] = ""
                i += 1
                continue

            if self._in_define:
                if full_line.strip() == 'endef':
                    self._in_define = False
                    self._define_var = None
                else:
                    if self._define_var:  # Only append if we have a valid variable name
                        self.analysis.variables[self._define_var] += full_line + '\n'
                i += 1
                continue

            # Handle comments (but check for target descriptions)
            if full_line.strip().startswith('#'):
                if current_target and not in_recipe and not current_target.description:
                    desc = full_line.strip().lstrip('#').strip()
                    if desc:
                        current_target.description = desc
                i += 1
                continue

            # Handle conditional directives
            if self._handle_conditional(full_line):
                i += 1
                continue

            # Skip if we're in a false conditional branch
            if self._in_false_conditional():
                i += 1
                continue

            # Variable definitions
            if self._is_variable_definition(full_line):
                self._parse_variable(full_line)
                i += 1
                continue

            # Include directives
            if full_line.strip().startswith(('include', '-include', 'sinclude')):
                parts = full_line.strip().split(None, 1)
                if len(parts) > 1:
                    self.analysis.includes.extend(parts[1].split())
                i += 1
                continue

            # Special targets
            if full_line.strip().startswith('.PHONY:'):
                phony_targets = full_line.split(':', 1)[1].strip().split()
                for target_name in phony_targets:
                    if target_name in self.analysis.targets:
                        self.analysis.targets[target_name].is_phony = True
                    else:
                        # Create placeholder for phony targets we haven't seen yet
                        target = MakefileTarget(name=target_name, is_phony=True)
                        self.analysis.targets[target_name] = target
                i += 1
                continue

            # Target definitions (including pattern rules and double-colon rules)
            if self._is_target_definition(full_line) and not full_line.startswith('\t'):
                target_info = self._parse_target_line(full_line)
                if target_info:
                    current_target = target_info
                    in_recipe = True
                i += 1
                continue

            # Recipe commands
            if full_line.startswith('\t') and current_target:
                command = full_line[1:]  # Remove leading tab
                if command.strip():
                    # Remove @ prefix if present
                    if command.strip().startswith('@'):
                        command = command.strip()[1:]
                    current_target.commands.append(command)

                    # Check for script calls
                    for pattern in self.SCRIPT_PATTERNS:
                        match = pattern.search(command)
                        if match:
                            script_name = match.group(1) if match.lastindex == 1 else match.group(2)
                            current_target.calls_scripts.append(script_name)

                    # Check for tool usage
                    for tool, pattern in self.TOOL_PATTERNS.items():
                        if pattern.search(command):
                            if tool == 'helm':
                                current_target.uses_helm = True
                            elif tool == 'kubectl':
                                current_target.uses_kubectl = True
                            elif tool == 'oc':
                                current_target.uses_oc = True
                            self.analysis.detected_tools.add(tool)
            else:
                in_recipe = False

            i += 1

    def _is_variable_definition(self, line: str) -> bool:
        """Check if a line is a variable definition.

        According to GNU Make manual, variable definitions can use:
        =, :=, ::=, +=, ?=, !=
        """
        # Skip lines that start with tab (these are commands)
        if line.startswith('\t'):
            return False
        
        # Check for specific assignment operators in order of precedence
        for op in ['::=', ':=', '!=', '?=', '+=', '=']:
            if op in line:
                # For plain '=' we need to distinguish from target definitions
                if op == '=' and ':' in line:
                    # Check if the ':' comes before the '='
                    colon_pos = line.find(':')
                    equals_pos = line.find('=')
                    if colon_pos < equals_pos and colon_pos != -1:
                        # This looks like a target definition with = in the dependencies
                        continue
                return True
        
        return False

    def _is_target_definition(self, line: str) -> bool:
        """Check if a line is a target definition.

        Handles:
        - Simple targets: target: dependencies
        - Pattern rules: %.o: %.c
        - Double-colon rules: target:: dependencies
        """
        # Must contain a colon
        if ':' not in line:
            return False

        # Check if it's a variable assignment with := or ::=
        if any(op in line.split(':')[0] for op in ['=', '?', '+', '!']):
            return False

        # It's likely a target
        return True

    def _parse_target_line(self, line: str) -> Optional[MakefileTarget]:
        """Parse a target line and return a MakefileTarget object."""
        # Check for double-colon rule
        is_double_colon = '::' in line and not ':::' in line

        if is_double_colon:
            parts = line.split('::', 1)
        else:
            parts = line.split(':', 1)

        if len(parts) < 2:
            return None

        target_part = parts[0].strip()
        deps_part = parts[1].strip() if len(parts) > 1 else ""

        # Check if it's a pattern rule
        is_pattern = '%' in target_part

        # Parse multiple targets
        targets = target_part.split()
        dependencies = deps_part.split() if deps_part else []

        # Create target object(s)
        for target_name in targets:
            target = MakefileTarget(
                name=target_name,
                dependencies=dependencies,
                is_pattern_rule=is_pattern,
                is_double_colon=is_double_colon
            )

            if is_pattern:
                self.analysis.pattern_rules.append(target)
            else:
                # For double-colon rules, append to existing target
                if is_double_colon and target_name in self.analysis.targets:
                    existing = self.analysis.targets[target_name]
                    existing.dependencies.extend(dependencies)
                    return existing
                else:
                    self.analysis.targets[target_name] = target

        # Return the last target created (for setting as current_target)
        return target

    def _handle_conditional(self, line: str) -> bool:
        """Handle conditional directives (ifeq, ifdef, ifndef, else, endif)."""
        stripped = line.strip()

        if stripped.startswith(('ifeq', 'ifneq', 'ifdef', 'ifndef')):
            # For now, we'll assume all conditionals are true
            # A full implementation would need to evaluate the conditions
            self._conditional_stack.append(True)
            return True
        elif stripped == 'else':
            if self._conditional_stack:
                self._conditional_stack[-1] = not self._conditional_stack[-1]
            return True
        elif stripped == 'endif':
            if self._conditional_stack:
                self._conditional_stack.pop()
            return True

        return False

    def _in_false_conditional(self) -> bool:
        """Check if we're currently in a false conditional branch."""
        return any(not cond for cond in self._conditional_stack)

    def _parse_variable(self, line: str) -> None:
        """Parse variable definition from line.

        Handles all GNU Make assignment operators:
        =   Recursively expanded
        :=  Simply expanded
        ::= Simply expanded (POSIX)
        +=  Appending
        ?=  Conditional (only if not defined)
        !=  Shell assignment
        """
        # Find the assignment operator
        for op in ['::=', ':=', '!=', '?=', '+=', '=']:
            if op in line:
                parts = line.split(op, 1)
                if len(parts) == 2:
                    var_name = parts[0].strip()
                    var_value = parts[1].strip()

                    if op == '+=':
                        # Append to existing value
                        if var_name in self.analysis.variables:
                            self.analysis.variables[var_name] += ' ' + var_value
                        else:
                            self.analysis.variables[var_name] = var_value
                    elif op == '?=':
                        # Only set if not already defined
                        if var_name not in self.analysis.variables:
                            self.analysis.variables[var_name] = var_value
                    else:
                        # Regular assignment
                        self.analysis.variables[var_name] = var_value
                break

    def _detect_tools(self) -> None:
        """Detect which deployment tools are used in the Makefile."""
        # Already detected during parsing, but we can do additional analysis here
        pass

    def _identify_deployment_targets(self) -> None:
        """Identify install and uninstall targets."""
        install_candidates = []
        uninstall_candidates = []

        for target_name, target in self.analysis.targets.items():
            lower_name = target_name.lower()

            # Skip pattern rules for this analysis
            if target.is_pattern_rule:
                continue

            # Check for install targets
            if any(keyword in lower_name for keyword in self.INSTALL_KEYWORDS):
                self.analysis.has_install_target = True
                install_candidates.append(target_name)

            # Check for uninstall targets
            if any(keyword in lower_name for keyword in self.UNINSTALL_KEYWORDS):
                self.analysis.has_uninstall_target = True
                uninstall_candidates.append(target_name)

        # Set install flow - prefer exact match, otherwise use first candidate
        if 'install' in self.analysis.targets:
            self.analysis.install_flow = ['install']
        elif install_candidates:
            self.analysis.install_flow = [install_candidates[0]]

        # Set uninstall flow - prefer exact match, otherwise use first candidate
        if 'uninstall' in self.analysis.targets:
            self.analysis.uninstall_flow = ['uninstall']
        elif uninstall_candidates:
            self.analysis.uninstall_flow = [uninstall_candidates[0]]

    def _trace_target_flow(self, target_type: str) -> None:
        """Trace the execution flow for install or uninstall targets."""
        if target_type == 'install':
            flow_list = self.analysis.install_flow
        else:
            flow_list = self.analysis.uninstall_flow

        if not flow_list:
            # Find the most likely target
            for keyword in (self.INSTALL_KEYWORDS if target_type == 'install' else self.UNINSTALL_KEYWORDS):
                for target_name in self.analysis.targets:
                    if keyword in target_name.lower():
                        flow_list.append(target_name)
                        break
                if flow_list:
                    break

        # Trace dependencies
        if flow_list:
            self._trace_dependencies(flow_list[0], flow_list, set())

    def _trace_dependencies(self, target_name: str, flow_list: List[str], visited: Set[str]) -> None:
        """Recursively trace target dependencies."""
        if target_name in visited:
            return

        visited.add(target_name)

        if target_name not in self.analysis.targets:
            return

        target = self.analysis.targets[target_name]

        # Add dependencies first (they execute before the target)
        for dep in target.dependencies:
            # Skip automatic variables and pattern rules
            if dep.startswith('$') or '%' in dep:
                continue

            if dep not in flow_list and dep in self.analysis.targets:
                # Insert dependencies before the current target
                insert_index = flow_list.index(target_name)
                flow_list.insert(insert_index, dep)
                self._trace_dependencies(dep, flow_list, visited)

    def _analyze_called_scripts(self) -> None:
        """Analyze scripts called from Makefile targets."""
        all_scripts = set()
        for target in self.analysis.targets.values():
            all_scripts.update(target.calls_scripts)

        for script in all_scripts:
            script_path = self.makefile_dir / script
            if script_path.exists():
                log_info(f"  Found script: {script}")
                # TODO: Implement script analysis

    def _analyze_variable_expansion(self, verbose: bool = False) -> None:
        """Analyze variable expansion in Makefile targets."""
        if not VARIABLE_EXPANSION_AVAILABLE:
            if verbose:
                log_warn("Variable expansion analysis not available")
            return

        try:
            log_info("Analyzing variable expansion...")
            
            # Create variable expander
            expander = VariableExpander(
                variables=self.analysis.variables,
                base_path=self.makefile_dir
            )
            
            # Expand variables in all targets
            expansion_results = expander.expand_all_targets(self.analysis.targets)
            self.analysis.variable_expansion_results = expansion_results
            
            # Get expansion summary
            self.analysis.expansion_summary = expander.get_expansion_summary()
            
            if verbose:
                log_info(f"  Variables expanded: {len(expansion_results)}")
                log_info(f"  Total expansions: {self.analysis.expansion_summary.get('total_expansions', 0)}")
                
                # Show variables used
                vars_used = self.analysis.expansion_summary.get('variables_used', [])
                if vars_used:
                    log_info(f"  Variables used: {', '.join(vars_used[:5])}")
                    
                # Show functions used
                funcs_used = self.analysis.expansion_summary.get('functions_used', [])
                if funcs_used:
                    log_info(f"  Functions used: {', '.join(funcs_used[:5])}")
                    
                # Show unexpanded variables
                unexpanded = self.analysis.expansion_summary.get('unexpanded_vars', [])
                if unexpanded:
                    log_warn(f"  Unexpanded variables: {', '.join(unexpanded[:5])}")
                    
        except Exception as e:
            log_warn(f"Variable expansion analysis failed: {e}")
            if verbose:
                import traceback
                traceback.print_exc()

    def generate_flow_diagram(self, target_type: str = 'install') -> str:
        """Generate ASCII flow diagram for install or uninstall process."""
        return self._generate_flow_diagram_from_analysis(self.analysis, target_type)

    @staticmethod
    def _generate_flow_diagram_from_analysis(analysis: MakefileAnalysis, target_type: str = 'install') -> str:
        """Generate ASCII flow diagram from analysis data."""
        if target_type == 'install':
            flow = analysis.install_flow
            title = "Installation Flow"
        else:
            flow = analysis.uninstall_flow
            title = "Uninstallation Flow"

        if not flow:
            return f"No {target_type} targets found in Makefile"

        # Build the diagram
        diagram = []
        diagram.append(f"\n{title}")
        diagram.append("=" * len(title))
        diagram.append("")

        # Show the main flow
        for i, target_name in enumerate(flow):
            target = analysis.targets.get(target_name)
            if not target:
                # Create a placeholder target for missing ones
                target = MakefileTarget(name=target_name)

            # Ensure target_name is not empty
            if not target_name or not target_name.strip():
                target_name = f"target_{i}"

            # Target box
            box_content = target_name  # Remove brackets - the box itself provides the visual boundary
            if target.description:
                box_content += f" - {target.description}"

            diagram.append(f"┌{'─' * (len(box_content) + 2)}┐")
            diagram.append(f"│ {box_content} │")
            diagram.append(f"└{'─' * (len(box_content) + 2)}┘")

            # Show key commands
            if target.commands:
                diagram.append("  │")
                for cmd in target.commands[:3]:  # Show first 3 commands
                    # Simplify command for display
                    if len(cmd) > 60:
                        cmd = cmd[:57] + "..."
                    diagram.append(f"  ├─> {cmd}")

                if len(target.commands) > 3:
                    diagram.append(f"  └─> ... ({len(target.commands) - 3} more commands)")
                else:
                    # Change last ├ to └
                    if diagram[-1].startswith("  ├"):
                        diagram[-1] = diagram[-1].replace("├", "└", 1)

            # Show tools used
            tools = []
            if target.uses_helm:
                tools.append("Helm")
            if target.uses_kubectl:
                tools.append("kubectl")
            if target.uses_oc:
                tools.append("oc")

            if tools:
                diagram.append(f"      Tools: {', '.join(tools)}")

            # Show called scripts
            if target.calls_scripts:
                diagram.append(f"      Scripts: {', '.join(target.calls_scripts)}")

            # Arrow to next target
            if i < len(flow) - 1:
                diagram.append("  │")
                diagram.append("  ▼")

        return '\n'.join(diagram)

    def print_analysis(self) -> None:
        """Print formatted analysis results."""
        console.print(f"\n[bold yellow]Makefile Analysis: {self.makefile_path.name}[/bold yellow]")

        # Summary
        console.print(f"\nTargets found: {len(self.analysis.targets)}")
        console.print(f"Pattern rules: {len(self.analysis.pattern_rules)}")
        console.print(f"Variables defined: {len(self.analysis.variables)}")

        if self.analysis.detected_tools:
            console.print(f"Tools detected: {', '.join(sorted(self.analysis.detected_tools))}")

        # Variable expansion summary
        if self.analysis.expansion_summary:
            console.print("\n[cyan]Variable Expansion Summary:[/cyan]")
            summary = self.analysis.expansion_summary
            console.print(f"  Total expansions: {summary.get('total_expansions', 0)}")
            
            vars_used = summary.get('variables_used', [])
            if vars_used:
                console.print(f"  Variables used: {', '.join(vars_used[:10])}")
                if len(vars_used) > 10:
                    console.print(f"    ... and {len(vars_used) - 10} more")
            
            funcs_used = summary.get('functions_used', [])
            if funcs_used:
                console.print(f"  Functions used: {', '.join(funcs_used)}")
            
            auto_vars = summary.get('automatic_vars_used', [])
            if auto_vars:
                console.print(f"  Automatic variables: {', '.join(auto_vars)}")
            
            unexpanded = summary.get('unexpanded_vars', [])
            if unexpanded:
                console.print(f"  [yellow]Unexpanded variables: {', '.join(unexpanded[:5])}[/yellow]")
                if len(unexpanded) > 5:
                    console.print(f"    [yellow]... and {len(unexpanded) - 5} more[/yellow]")

        # Key targets
        console.print("\n[cyan]Key Targets:[/cyan]")
        for target_name, target in self.analysis.targets.items():
            if any(kw in target_name.lower() for kw in self.INSTALL_KEYWORDS + self.UNINSTALL_KEYWORDS):
                console.print(f"  • {target_name}", end="")
                if target.description:
                    console.print(f" - {target.description}", end="")
                if target.is_phony:
                    console.print(" [.PHONY]", end="")
                if target.is_double_colon:
                    console.print(" [::]", end="")
                console.print()
                
                # Show variable expansion for this target
                if self.analysis.variable_expansion_results.get(target_name):
                    expansion_data = self.analysis.variable_expansion_results[target_name]
                    if expansion_data.get('variables_used'):
                        console.print(f"    Variables: {', '.join(sorted(expansion_data['variables_used']))}")
                    if expansion_data.get('functions_used'):
                        console.print(f"    Functions: {', '.join(sorted(expansion_data['functions_used']))}")

        # Pattern rules
        if self.analysis.pattern_rules:
            console.print("\n[cyan]Pattern Rules:[/cyan]")
            for rule in self.analysis.pattern_rules[:5]:  # Show first 5
                console.print(f"  • {rule.name}")

        # Show expanded commands for key targets
        if self.analysis.variable_expansion_results:
            console.print("\n[cyan]Expanded Commands (Key Targets):[/cyan]")
            for target_name in self.analysis.install_flow + self.analysis.uninstall_flow:
                if target_name in self.analysis.variable_expansion_results:
                    expansion_data = self.analysis.variable_expansion_results[target_name]
                    commands = expansion_data.get('commands', [])
                    if commands:
                        console.print(f"\n  Target: [bold]{target_name}[/bold]")
                        for i, cmd_data in enumerate(commands[:3]):  # Show first 3 commands
                            original = cmd_data.get('original', '')
                            expanded = cmd_data.get('expanded', '')
                            if original != expanded:
                                console.print(f"    {i+1}. [dim]{original}[/dim]")
                                console.print(f"       → {expanded}")
                            else:
                                console.print(f"    {i+1}. {original}")
                        if len(commands) > 3:
                            console.print(f"       ... and {len(commands) - 3} more commands")

        # Flow diagrams
        if self.analysis.has_install_target:
            console.print(self.generate_flow_diagram('install'))

        if self.analysis.has_uninstall_target:
            console.print(self.generate_flow_diagram('uninstall'))