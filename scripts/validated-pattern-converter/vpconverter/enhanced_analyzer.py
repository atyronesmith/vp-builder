"""
Enhanced Helm chart analyzer with pattern detection capabilities.

This module provides deep analysis of Helm charts including:
- Template parsing and resource extraction
- Architecture pattern detection
- Component identification
- Security analysis
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Dict, Any, Optional
import yaml
import re

from .models import HelmChart, AnalysisResult
from .utils import log_info, log_warn, console, read_yaml


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
class ArchitecturePattern:
    """Represents a detected architecture pattern."""
    name: str
    confidence: float  # 0.0 to 1.0
    evidence: List[str] = field(default_factory=list)
    description: str = ""


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
        """Detect architecture patterns."""
        patterns = []

        # AI/ML Pattern Detection
        ai_pattern = self._detect_ai_ml_pattern(components)
        if ai_pattern.confidence > 0.3:
            patterns.append(ai_pattern)

        # Microservices Pattern
        microservices = self._detect_microservices_pattern(resources)
        if microservices.confidence > 0.3:
            patterns.append(microservices)

        # Data Processing Pattern
        data_pattern = self._detect_data_pattern(components)
        if data_pattern.confidence > 0.3:
            patterns.append(data_pattern)

        # Deployment Patterns
        deployment_pattern = self._detect_deployment_patterns()
        if deployment_pattern.confidence > 0.3:
            patterns.append(deployment_pattern)

        # UI Patterns
        ui_pattern = self._detect_ui_patterns()
        if ui_pattern.confidence > 0.3:
            patterns.append(ui_pattern)

        # Cloud-Native Patterns
        cloud_pattern = self._detect_cloud_native_patterns()
        if cloud_pattern.confidence > 0.3:
            patterns.append(cloud_pattern)

        return patterns

    def _detect_ai_ml_pattern(self, components: List[ChartComponent]) -> ArchitecturePattern:
        """Detect AI/ML patterns."""
        evidence = []
        confidence = 0.0

        # Expanded AI/ML keywords
        ai_keywords = ['llm', 'llama', 'gpt', 'bert', 'transformer', 'pytorch',
                      'tensorflow', 'mlflow', 'model', 'inference', 'embedding',
                      'vector', 'rag', 'retrieval', 'augmented', 'ollama', 'llamastack']

        # Check components
        for comp in components:
            comp_str = f"{comp.name} {comp.description} {comp.image or ''}".lower()
            for keyword in ai_keywords:
                if keyword in comp_str:
                    evidence.append(f"AI/ML component: {comp.name} (contains '{keyword}')")
                    confidence += 0.3
                    break

        # Check for vector databases
        vector_dbs = ['pgvector', 'chroma', 'pinecone', 'weaviate', 'qdrant', 'milvus']
        for comp in components:
            if any(db in str(comp).lower() for db in vector_dbs):
                evidence.append(f"Vector database: {comp.name}")
                confidence += 0.4

        # Check values for GPU resources
        if 'resources' in str(self.values).lower() and 'gpu' in str(self.values).lower():
            evidence.append("GPU resources configured")
            confidence += 0.3

        # Enhanced RAG pattern detection
        chart_name = self.chart_path.name.lower()
        if 'rag' in chart_name:
            evidence.append("RAG architecture (chart name indicates RAG)")
            confidence += 0.5
        else:
            # Check for RAG indicators in templates and values
            rag_indicators = ['retrieval', 'augmented', 'generation', 'knowledge', 'documents']
            template_content = str(self.templates).lower()
            values_content = str(self.values).lower()

            rag_matches = sum(1 for indicator in rag_indicators
                            if indicator in template_content or indicator in values_content)
            if rag_matches >= 3:
                evidence.append("RAG (Retrieval-Augmented Generation) pattern detected")
                confidence += 0.4

        # Streamlit UI detection (common for AI demos)
        if 'streamlit' in str(self.values).lower() or 'streamlit' in str(self.templates).lower():
            evidence.append("Streamlit-based AI interface")
            confidence += 0.2

        return ArchitecturePattern(
            name="AI/ML Pipeline",
            confidence=min(confidence, 1.0),
            evidence=evidence,
            description="Machine learning or AI capabilities detected"
        )

    def _detect_microservices_pattern(self, resources: Dict[str, List[str]]) -> ArchitecturePattern:
        """Detect microservices patterns."""
        evidence = []
        confidence = 0.0

        # Multiple services indicate microservices
        service_count = len(resources.get('Service', []))
        if service_count > 3:
            evidence.append(f"Multiple services ({service_count})")
            confidence += 0.3

        # Check for API gateway/ingress
        if 'Ingress' in resources or 'Route' in resources:
            evidence.append("API Gateway/Ingress present")
            confidence += 0.3

        # Service mesh indicators
        for template in self.templates:
            template_str = str(template).lower()
            if any(mesh in template_str for mesh in ['istio', 'linkerd', 'consul']):
                evidence.append("Service mesh detected")
                confidence += 0.4
                break

        return ArchitecturePattern(
            name="Microservices Architecture",
            confidence=min(confidence, 1.0),
            evidence=evidence,
            description="Distributed service architecture"
        )

    def _detect_data_pattern(self, components: List[ChartComponent]) -> ArchitecturePattern:
        """Detect data processing patterns."""
        evidence = []
        confidence = 0.0

        # Data processing keywords
        data_keywords = ['kafka', 'spark', 'flink', 'airflow', 'etl', 'pipeline',
                        'stream', 'batch', 'queue', 'pubsub']

        for comp in components:
            comp_str = str(comp).lower()
            for keyword in data_keywords:
                if keyword in comp_str:
                    evidence.append(f"Data processing: {comp.name}")
                    confidence += 0.4
                    break

        # Check for databases
        db_keywords = ['postgres', 'mysql', 'mongodb', 'redis', 'cassandra']
        db_count = sum(1 for comp in components
                      if any(db in str(comp).lower() for db in db_keywords))

        if db_count > 1:
            evidence.append(f"Multiple data stores ({db_count})")
            confidence += 0.3

        return ArchitecturePattern(
            name="Data Processing Pipeline",
            confidence=min(confidence, 1.0),
            evidence=evidence,
            description="Data pipeline or ETL workflow"
        )

    def _detect_deployment_patterns(self) -> ArchitecturePattern:
        """Detect deployment and lifecycle patterns."""
        evidence = []
        confidence = 0.0

        # Container registry patterns
        registries = set()
        for template in self.templates:
            if template.get('kind') == 'Deployment':
                containers = template.get('spec', {}).get('template', {}).get('spec', {}).get('containers', [])
                for container in containers:
                    image = container.get('image', '')
                    if image and '/' in image:
                        registry = image.split('/')[0]
                        registries.add(registry)

        if registries:
            evidence.append(f"Container registries: {', '.join(registries)}")
            confidence += 0.1

        # Check for private registries
        private_indicators = ['quay.io', 'gcr.io', 'registry.redhat.io', 'localhost']
        for registry in registries:
            if any(indicator in registry for indicator in private_indicators):
                evidence.append("Private/Enterprise container registry")
                confidence += 0.2
                break

        # Health checks
        health_check_types = set()
        for template in self.templates:
            if template.get('kind') == 'Deployment':
                containers = template.get('spec', {}).get('template', {}).get('spec', {}).get('containers', [])
                for container in containers:
                    if 'livenessProbe' in container:
                        health_check_types.add('liveness')
                    if 'readinessProbe' in container:
                        health_check_types.add('readiness')
                    if 'startupProbe' in container:
                        health_check_types.add('startup')

        if health_check_types:
            evidence.append(f"Health checks: {', '.join(health_check_types)}")
            confidence += 0.3

        # Rolling update strategy
        for template in self.templates:
            if template.get('kind') == 'Deployment':
                strategy = template.get('spec', {}).get('strategy', {})
                if strategy.get('type') == 'RollingUpdate':
                    evidence.append("Rolling update strategy")
                    confidence += 0.2

        return ArchitecturePattern(
            name="Deployment Patterns",
            confidence=min(confidence, 1.0),
            evidence=evidence,
            description="Container deployment and lifecycle management"
        )

    def _detect_ui_patterns(self) -> ArchitecturePattern:
        """Detect user interface patterns."""
        evidence = []
        confidence = 0.0

        # Frontend frameworks
        ui_frameworks = ['streamlit', 'react', 'angular', 'vue', 'flask', 'django', 'fastapi', 'nginx']

        # Check in container images
        for template in self.templates:
            if template.get('kind') == 'Deployment':
                containers = template.get('spec', {}).get('template', {}).get('spec', {}).get('containers', [])
                for container in containers:
                    image = container.get('image', '').lower()
                    for framework in ui_frameworks:
                        if framework in image:
                            evidence.append(f"UI framework: {framework}")
                            confidence += 0.3

        # Check values for UI configurations
        values_str = str(self.values).lower()
        for framework in ui_frameworks:
            if framework in values_str:
                evidence.append(f"UI technology: {framework}")
                confidence += 0.2

        # Check for web service ports
        ui_ports = [80, 443, 3000, 8080, 8501, 9000]  # 8501 is Streamlit default
        for template in self.templates:
            if template.get('kind') == 'Service':
                ports = template.get('spec', {}).get('ports', [])
                for port_spec in ports:
                    port = port_spec.get('port') or port_spec.get('targetPort')
                    if port in ui_ports:
                        evidence.append(f"Web service port: {port}")
                        confidence += 0.1

        # Routes/Ingress for web access
        route_count = len([t for t in self.templates if t.get('kind') in ['Route', 'Ingress']])
        if route_count > 0:
            evidence.append(f"Web routing ({route_count} routes/ingress)")
            confidence += 0.2

        return ArchitecturePattern(
            name="User Interface",
            confidence=min(confidence, 1.0),
            evidence=evidence,
            description="Web-based user interface"
        )

    def _detect_cloud_native_patterns(self) -> ArchitecturePattern:
        """Detect cloud-native and platform patterns."""
        evidence = []
        confidence = 0.0

        # OpenShift specific resources
        openshift_resources = ['Route', 'DeploymentConfig', 'ImageStream', 'BuildConfig']
        openshift_count = sum(1 for template in self.templates
                             if template.get('kind') in openshift_resources)

        if openshift_count > 0:
            evidence.append(f"OpenShift resources ({openshift_count})")
            confidence += 0.4

        # Service mesh annotations
        service_mesh_annotations = ['sidecar.istio.io', 'linkerd.io', 'consul.hashicorp.com']
        for template in self.templates:
            annotations = template.get('metadata', {}).get('annotations', {})
            for annotation in annotations:
                if any(mesh in annotation for mesh in service_mesh_annotations):
                    evidence.append("Service mesh integration")
                    confidence += 0.3
                    break

        # Operator patterns
        if any('operator' in str(template).lower() for template in self.templates):
            evidence.append("Kubernetes Operator pattern")
            confidence += 0.3

        # Cloud provider specific
        cloud_indicators = ['aws', 'azure', 'gcp']
        template_str = str(self.templates).lower()
        for cloud in cloud_indicators:
            if cloud in template_str:
                evidence.append(f"Cloud provider: {cloud.upper()}")
                confidence += 0.2

        return ArchitecturePattern(
            name="Cloud-Native Patterns",
            confidence=min(confidence, 1.0),
            evidence=evidence,
            description="Cloud-native deployment patterns"
        )

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