"""
Enhanced Helm chart analyzer with pattern detection capabilities.

This module provides deep analysis of Helm charts including:
- Template parsing and resource extraction
- Architecture pattern detection using rule engine
- Component identification
- Security analysis
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Dict, Any, Optional
import yaml
import re

from .models import HelmChart, AnalysisResult, ArchitecturePattern
from .utils import log_info, log_warn, console, read_yaml
from .rules_engine import RuleEngine, PatternDefinition, DetectionRule, load_patterns


@dataclass
class ChartComponent:
    """Represents a component within a Helm chart."""
    name: str
    type: str  # container, dependency, service, etc.
    image: Optional[str] = None
    ports: List[int] = field(default_factory=list)
    description: str = ""
    source_template: Optional[str] = None


@dataclass
class EnhancedChartAnalysis:
    """Enhanced analysis results for a Helm chart."""
    chart: HelmChart
    components: List[ChartComponent] = field(default_factory=list)
    resources: Dict[str, List[str]] = field(default_factory=dict)  # kind -> names
    patterns: List[ArchitecturePattern] = field(default_factory=list)
    security_features: List[str] = field(default_factory=list)
    scaling_features: List[str] = field(default_factory=list)


class EnhancedHelmAnalyzer:
    """Enhanced Helm chart analyzer with deep inspection capabilities."""

    def __init__(self, chart_path: Path):
        self.chart_path = chart_path
        self.templates_path = chart_path / "templates"
        self.templates: List[Dict[str, Any]] = []
        self.values: Dict[str, Any] = {}
        self.rule_engine = RuleEngine()
        self.pattern_definitions = load_patterns()

    def analyze(self) -> EnhancedChartAnalysis:
        """Perform enhanced analysis of the Helm chart."""
        # Load chart metadata
        chart_yaml = read_yaml(self.chart_path / "Chart.yaml")

        # Create basic HelmChart object
        chart = HelmChart(
            name=chart_yaml.get('name', 'unknown'),
            path=self.chart_path,
            version=chart_yaml.get('version'),
            app_version=chart_yaml.get('appVersion'),
            description=chart_yaml.get('description'),
            chart_type=chart_yaml.get('type', 'application'),
            dependencies=chart_yaml.get('dependencies', [])
        )

        # Load values
        values_file = self.chart_path / "values.yaml"
        if values_file.exists():
            self.values = read_yaml(values_file)
            chart.has_values = True

        # Parse templates
        self._parse_templates()

        # Extract components
        components = self._extract_components()

        # Extract resources by kind
        resources = self._extract_resources_by_kind()

        # Detect patterns
        patterns = self._detect_patterns(components, resources)

        # Analyze security features
        security_features = self._analyze_security()

        # Analyze scaling features
        scaling_features = self._analyze_scaling()

        return EnhancedChartAnalysis(
            chart=chart,
            components=components,
            resources=resources,
            patterns=patterns,
            security_features=security_features,
            scaling_features=scaling_features
        )

    def _parse_templates(self) -> None:
        """Parse all template files and extract Kubernetes resources."""
        if not self.templates_path.exists():
            return

        for template_file in self.templates_path.glob("*.yaml"):
            if template_file.name.startswith('_'):  # Skip helpers
                continue

            try:
                with open(template_file, 'r') as f:
                    content = f.read()

                # Handle multi-document YAML
                docs = content.split('\n---\n')
                for doc in docs:
                    if doc.strip():
                        try:
                            # Simple approach: try to parse as YAML
                            # In practice, we'd need to handle Go templates
                            parsed = self._parse_template_doc(doc)
                            if parsed:
                                parsed['_source_file'] = template_file.name
                                self.templates.append(parsed)
                        except Exception:
                            pass
            except Exception as e:
                log_warn(f"Could not parse {template_file}: {e}")

    def _parse_template_doc(self, doc: str) -> Optional[Dict[str, Any]]:
        """Parse a single template document, handling Go templates."""
        # Remove common Go template constructs for parsing
        cleaned = re.sub(r'{{\s*[-\s]*.*?[-\s]*\s*}}', 'TEMPLATE_VALUE', doc)

        try:
            parsed = yaml.safe_load(cleaned)
            if isinstance(parsed, dict) and 'kind' in parsed:
                return parsed
        except:
            pass
        return None

    def _extract_components(self) -> List[ChartComponent]:
        """Extract components from templates and dependencies."""
        components = []

        # Extract from Deployments
        for template in self.templates:
            if template.get('kind') == 'Deployment':
                deployment_name = template.get('metadata', {}).get('name', 'unknown')
                spec = template.get('spec', {})
                pod_spec = spec.get('template', {}).get('spec', {})

                for container in pod_spec.get('containers', []):
                    # Extract more details
                    ports = [p.get('containerPort') for p in container.get('ports', []) if 'containerPort' in p]
                    env_vars = container.get('env', [])

                    component = ChartComponent(
                        name=container.get('name', deployment_name),
                        type='container',
                        image=container.get('image', ''),
                        ports=ports,
                        description=f"Container in {deployment_name} with {len(env_vars)} env vars",
                        source_template=template.get('_source_file')
                    )
                    components.append(component)

        # Extract from dependencies with classification
        chart_yaml = read_yaml(self.chart_path / "Chart.yaml")
        for dep in chart_yaml.get('dependencies', []):
            dep_type = self._classify_dependency_type(dep.get('name', ''))
            component = ChartComponent(
                name=dep.get('name', 'unknown'),
                type=f'dependency-{dep_type}',
                description=f"{dep_type.title()} dependency: {dep.get('repository', 'unknown')}"
            )
            components.append(component)

        return components

    def _classify_dependency_type(self, dep_name: str) -> str:
        """Classify dependency type based on name."""
        dep_lower = dep_name.lower()

        if any(db in dep_lower for db in ['postgres', 'mysql', 'mongo', 'redis', 'vector', 'pgvector']):
            return 'database'
        elif any(storage in dep_lower for storage in ['minio', 's3', 'storage']):
            return 'storage'
        elif any(ai in dep_lower for ai in ['llm', 'llama', 'model', 'ai', 'ollama']):
            return 'ai-service'
        elif any(web in dep_lower for web in ['nginx', 'apache', 'traefik']):
            return 'web-server'
        elif any(msg in dep_lower for msg in ['kafka', 'rabbit', 'queue', 'nats']):
            return 'messaging'
        elif any(tool in dep_lower for tool in ['weather', 'mcp', 'tool']):
            return 'tool'
        elif any(pipeline in dep_lower for pipeline in ['pipeline', 'ingestion', 'configure']):
            return 'pipeline'
        else:
            return 'service'

    def _extract_resources_by_kind(self) -> Dict[str, List[str]]:
        """Group resources by their kind."""
        resources = {}

        for template in self.templates:
            kind = template.get('kind', 'Unknown')
            name = template.get('metadata', {}).get('name', 'unnamed')

            if kind not in resources:
                resources[kind] = []
            resources[kind].append(name)

        return resources

    def _detect_patterns(self, components: List[ChartComponent], resources: Dict[str, List[str]]) -> List[ArchitecturePattern]:
        """Detect architecture patterns using rule-based engine."""
        detected_patterns = []

        # Prepare analysis context
        context = self._build_analysis_context(components, resources)

        # Process each pattern definition
        for pattern_def in self.pattern_definitions:
            confidence = 0.0
            evidence = []

            # Apply each rule in the pattern
            for rule in pattern_def.rules:
                rule_match, rule_evidence = self._apply_rule(rule, context)
                if rule_match:
                    confidence += rule.confidence_boost
                    evidence.extend(rule_evidence)

            # Cap confidence at 1.0
            confidence = min(confidence, 1.0)

            # Only include patterns that meet minimum confidence
            if confidence >= pattern_def.min_confidence:
                pattern = ArchitecturePattern(
                    name=pattern_def.name,
                    confidence=confidence,
                    evidence=evidence,
                    description=pattern_def.description
                )
                detected_patterns.append(pattern)

        # Sort by confidence (highest first)
        detected_patterns.sort(key=lambda p: p.confidence, reverse=True)

        return detected_patterns

    def _build_analysis_context(self, components: List[ChartComponent], resources: Dict[str, List[str]]) -> Dict[str, Any]:
        """Build a comprehensive context for rule evaluation"""
        # Extract dependencies
        dependencies = []
        for dep in self.values.get('dependencies', []):
            dependencies.append(dep.get('name', ''))
        for comp in components:
            if comp.type.startswith('dependency'):
                dependencies.append(comp.name)

        # Extract all images
        images = []
        for comp in components:
            if comp.image:
                images.append(comp.image)

        # Count services
        service_count = len(resources.get('Service', []))

        # Extract ports
        ports = []
        for comp in components:
            if comp.ports:
                ports.extend(comp.ports)

        # Build context
        return {
            'chart_name': self.chart_path.name,
            'chart_yaml': read_yaml(self.chart_path / "Chart.yaml"),
            'values': self.values,
            'templates': self.templates,
            'components': components,
            'resources': resources,
            'dependencies': dependencies,
            'images': images,
            'service_count': service_count,
            'ports': ports,
            'content': str(self.templates) + str(self.values)  # For content searches
        }

    def _apply_rule(self, rule: DetectionRule, context: Dict[str, Any]) -> tuple[bool, List[str]]:
        """Apply a single detection rule and return (matched, evidence_list)"""
        evidence = []

        if rule.type == "dependency":
            for dep in context['dependencies']:
                matches = self.rule_engine.match(dep, rule.match_value, rule.match_mode, rule.case_sensitive)
                for match in matches:
                    evidence.append(rule.evidence_template.format(match=match))

        elif rule.type == "kind":
            kinds = [t.get('kind', '') for t in context['templates']]
            for kind in kinds:
                matches = self.rule_engine.match(kind, rule.match_value, rule.match_mode, rule.case_sensitive)
                for match in matches:
                    evidence.append(rule.evidence_template.format(match=match))

        elif rule.type == "image":
            for image in context['images']:
                matches = self.rule_engine.match(image, rule.match_value, rule.match_mode, rule.case_sensitive)
                for match in matches:
                    evidence.append(rule.evidence_template.format(match=match))

        elif rule.type == "content":
            matches = self.rule_engine.match(context['content'], rule.match_value, rule.match_mode, rule.case_sensitive)
            for match in matches:
                evidence.append(rule.evidence_template.format(match=match))

        elif rule.type == "api_version":
            api_versions = [t.get('apiVersion', '') for t in context['templates']]
            for api_version in api_versions:
                matches = self.rule_engine.match(api_version, rule.match_value, rule.match_mode, rule.case_sensitive)
                for match in matches:
                    evidence.append(rule.evidence_template.format(match=match))

        elif rule.type == "service_count":
            if rule.match_mode == "greater_than" and context['service_count'] > rule.match_value:
                evidence.append(rule.evidence_template.format(count=context['service_count']))

        elif rule.type == "chart_name":
            matches = self.rule_engine.match(context['chart_name'], rule.match_value, rule.match_mode, rule.case_sensitive)
            for match in matches:
                evidence.append(rule.evidence_template.format(match=match))

        elif rule.type == "port":
            for port in context['ports']:
                if isinstance(rule.match_value, list) and port in rule.match_value:
                    evidence.append(rule.evidence_template.format(match=port))

        elif rule.type == "annotation":
            for template in context['templates']:
                annotations = template.get('metadata', {}).get('annotations', {})
                for annotation_key in annotations.keys():
                    matches = self.rule_engine.match(annotation_key, rule.match_value, rule.match_mode, rule.case_sensitive)
                    for match in matches:
                        evidence.append(rule.evidence_template.format(match=match))

        return len(evidence) > 0, evidence

    # Remove old pattern detection methods as they're replaced by rule engine
    def _detect_ai_ml_pattern(self, components: List[ChartComponent]) -> ArchitecturePattern:
        """DEPRECATED: Use rule-based detection instead"""
        # This method is kept for backward compatibility but delegates to rule engine
        return ArchitecturePattern(name="AI/ML Pipeline", confidence=0.0, evidence=[], description="Use rule engine")

    def _detect_microservices_pattern(self, resources: Dict[str, List[str]]) -> ArchitecturePattern:
        """DEPRECATED: Use rule-based detection instead"""
        return ArchitecturePattern(name="Microservices", confidence=0.0, evidence=[], description="Use rule engine")

    def _detect_data_pattern(self, components: List[ChartComponent]) -> ArchitecturePattern:
        """DEPRECATED: Use rule-based detection instead"""
        return ArchitecturePattern(name="Data Processing", confidence=0.0, evidence=[], description="Use rule engine")

    def _detect_deployment_patterns(self) -> ArchitecturePattern:
        """DEPRECATED: Use rule-based detection instead"""
        return ArchitecturePattern(name="Deployment", confidence=0.0, evidence=[], description="Use rule engine")

    def _detect_ui_patterns(self) -> ArchitecturePattern:
        """DEPRECATED: Use rule-based detection instead"""
        return ArchitecturePattern(name="UI", confidence=0.0, evidence=[], description="Use rule engine")

    def _detect_cloud_native_patterns(self) -> ArchitecturePattern:
        """DEPRECATED: Use rule-based detection instead"""
        return ArchitecturePattern(name="Cloud Native", confidence=0.0, evidence=[], description="Use rule engine")

    def _analyze_security(self) -> List[str]:
        """Analyze security features."""
        features = []

        # Extract resources for this method
        resources = self._extract_resources_by_kind()

        # Check for RBAC
        rbac_kinds = ['Role', 'ClusterRole', 'RoleBinding', 'ClusterRoleBinding']
        if any(kind in resources for kind in rbac_kinds):
            features.append("RBAC configuration")

        # Check for TLS
        if any('tls' in str(template).lower() for template in self.templates):
            features.append("TLS/SSL encryption")

        # Check for secrets
        if 'Secret' in resources:
            features.append(f"Secrets management ({len(resources['Secret'])} secrets)")

        # Check for NetworkPolicy
        if 'NetworkPolicy' in resources:
            features.append("Network policies")

        # Check for security contexts
        for template in self.templates:
            if 'securityContext' in str(template):
                features.append("Pod security contexts")
                break

        return features

    def _analyze_scaling(self) -> List[str]:
        """Analyze scaling features."""
        features = []

        # Extract resources for this method
        resources = self._extract_resources_by_kind()

        # HPA
        if 'HorizontalPodAutoscaler' in resources:
            features.append("Horizontal Pod Autoscaling (HPA)")

        # Check for replicas > 1
        for template in self.templates:
            if template.get('kind') == 'Deployment':
                replicas = template.get('spec', {}).get('replicas')
                if isinstance(replicas, int) and replicas > 1:
                    features.append(f"Multi-replica deployment ({replicas} replicas)")

        # Resource limits
        for template in self.templates:
            if 'resources' in str(template) and ('limits' in str(template) or 'requests' in str(template)):
                features.append("Resource management (requests/limits)")
                break

        return features