# Validated Patterns Reference Documentation

This document serves as a comprehensive reference for Red Hat Validated Patterns based on the official documentation at https://validatedpatterns.io

## Table of Contents
1. [Overview](#overview)
2. [Key Concepts](#key-concepts)
3. [Architecture](#architecture)
4. [Quick Start Guide](#quick-start-guide)
5. [Frameworks](#frameworks)
6. [Values Files](#values-files)
7. [Workflow](#workflow)
8. [Infrastructure Requirements](#infrastructure-requirements)
9. [Secrets Management](#secrets-management)
10. [Pattern Structure](#pattern-structure)

## Overview

### What are Validated Patterns?
Validated Patterns are an advanced form of reference architectures that offer a streamlined approach to deploying complex business solutions. They represent deployable, testable software artifacts with automated deployment capabilities, focusing on:
- Pre-validated, automated deployment processes
- Reduced deployment risks and manual intervention
- Consistent and efficient multi-product solution implementations

### Core Characteristics
- **Purpose**: Provide automated deployment for complex business solutions
- **Design**: Built on successful deployment experiences incorporating multiple Red Hat products
- **Technology**: Leverage GitOps-based automation and continuous integration
- **Users**: IT architects, advanced developers, system administrators familiar with Kubernetes/OpenShift

### Unique Value Proposition
"Validated Patterns enhance reference architectures with automation and rigorous validation" - transforming conceptual frameworks into deployable, optimized software artifacts.

## Key Concepts

### Core Components

#### 1. Helm
- Package manager for Kubernetes
- Uses templating language for configuring applications
- Preferred mechanism for deploying applications in validated patterns

#### 2. GitOps
Management of cloud-native systems powered by Kubernetes with principles:
- Declarative configuration
- Versioned and immutable
- Automatically pulled
- Continuously reconciled

#### 3. ClusterGroups
- Organize and manage clusters with shared configurations
- Can represent single or multiple clusters
- Fundamental for pattern deployment and management

### Technical Elements

#### Applications
- Defined in Helm values files
- Specify deployment configurations
- Create Kubernetes resources (Deployments, Services, ConfigMaps)

#### Secrets Management
- Securely store sensitive information
- Integrated with HashiCorp Vault
- Support for certificates and credentials

## Architecture

### Multi-Cluster Support
Validated Patterns support hub-and-spoke architecture:
- **Hub Cluster**: Central management cluster
- **Managed Clusters**: Edge or regional clusters
- **GitOps Integration**: ArgoCD manages deployments

### Pattern Components
```
pattern-name/
├── charts/
│   ├── hub/          # Hub cluster applications
│   ├── region/       # Regional cluster applications
│   └── all/          # Common applications
├── values-*.yaml     # Environment-specific values
├── Makefile         # Pattern-specific build targets
├── common/          # Shared configuration (subtree)
└── scripts/         # Automation scripts
```

## Quick Start Guide

### Prerequisites
- OpenShift Container Platform 4.12 or later
- Cluster-admin privileges
- Minimum 8 CPU cores and 16GB RAM
- Dynamic storage class configured
- Access to public registries and GitHub

### Installation Steps
1. **Fork the Pattern Repository**
   ```bash
   # Fork on GitHub, then clone
   git clone https://github.com/YOUR-ORG/pattern-name
   cd pattern-name
   ```

2. **Create Secrets File**
   ```bash
   cp values-secret.yaml.template ~/values-secret.yaml
   # Edit with your credentials
   ```

3. **Customize Configuration**
   - Edit `values-global.yaml` for cluster-specific settings
   - Update repository URLs to point to your fork

4. **Deploy the Pattern**
   ```bash
   ./pattern.sh make install
   # Or use Validated Patterns Operator
   ```

5. **Verify Deployment**
   - Check operator status: `oc get operators`
   - Verify ArgoCD apps: `oc get applications -n openshift-gitops`

## Frameworks

### 1. OpenShift-based Validated Patterns Framework
- Most common deployment method
- Predefined configurations following best practices
- Validated by Red Hat
- GitOps-based with ArgoCD

### 2. Ansible GitOps Framework (AGOF)
- Alternative for non-Kubernetes environments
- Designed for Ansible Automation Platform
- Supports VMs in AWS or pre-provisioned infrastructure

### Common Framework Goals
- Secure and repeatable day-one deployment
- Maintenance automation for day-two operations
- Enable collaboration between teams

## Values Files

### Structure
Values files use YAML format with three main sections:

```yaml
global:
  # Shared configurations across charts
  pattern: pattern-name
  namespace: pattern-namespace
  
main:
  # Main cluster configuration
  clusterGroupName: hub
  
clusterGroup:
  # Cluster-specific configurations
  name: hub
  isHubCluster: true
  applications:
    - name: app1
      namespace: app1-ns
      project: default
      path: charts/hub/app1
```

### Hierarchy and Precedence
- Last defined value takes precedence
- Global values are inherited by all applications
- ClusterGroup values override global values
- Application-specific values override all others

### Best Practices
- Use descriptive variable names
- Keep secrets out of version control
- Use template files for sensitive data
- Document custom variables

## Workflow

### Pattern Consumption Workflow

1. **Preparation**
   - Fork pattern repository
   - Clone to local machine
   - Create secrets file (don't commit!)

2. **Customization**
   - Edit values files
   - Update git URLs
   - Configure cluster-specific settings

3. **Deployment**
   - Use pattern.sh script or operator
   - Monitor ArgoCD synchronization
   - Verify component deployment

### Development Workflow

1. **Pattern Development**
   - Start with existing pattern as template
   - Modify charts and values
   - Test in development cluster

2. **GitOps Integration**
   - Commit changes to git
   - ArgoCD detects and applies changes
   - Automated rollback if needed

## Infrastructure Requirements

### Platform Requirements
- **OpenShift Container Platform**: 4.16-4.18
- **Storage**: Dynamic StorageClass (ODF, LVM, or CephFS)
- **Registry**: Configured image registry

### Hardware Requirements (Pattern-Specific)
Some patterns require:
- Intel AMX processors
- Intel SGX (enabled in BIOS)
- Intel QAT support
- GPU acceleration

### Deployment Options
- Single cluster
- Multi-cluster (hub + managed)
- Cloud or on-premises
- Hybrid deployments

### Network Requirements
- Access to:
  - quay.io
  - registry.redhat.io
  - github.com
  - Pattern-specific repositories

## Secrets Management

### Principles
- **Never commit secrets to git**
- Use enterprise secret management
- Leverage specialized tools

### Implementation with HashiCorp Vault
- Centralized secret storage
- Policy-based access control
- Automatic secret rotation
- Integration with Kubernetes

### Secret Types
- Database passwords
- API tokens
- TLS certificates
- SSH keys
- Cloud credentials

### Best Practices
1. Use `values-secret.yaml` locally (never commit)
2. Configure Vault policies appropriately
3. Generate random passwords when possible
4. Implement secret rotation
5. Audit secret access

## Pattern Structure

### Standard Directory Layout
```
pattern-name/
├── charts/                 # Helm charts
│   ├── hub/               # Hub-specific apps
│   │   ├── app1/
│   │   └── app2/
│   ├── region/            # Edge cluster apps
│   └── all/               # Common apps
├── values-global.yaml     # Global configuration
├── values-hub.yaml        # Hub-specific values
├── values-region.yaml     # Region-specific values
├── values-secret.yaml.template  # Secret template
├── pattern.sh             # Deployment script
├── Makefile              # Build automation
├── common/               # Common framework (subtree)
└── scripts/              # Helper scripts
```

### Key Files

#### values-global.yaml
Defines pattern-wide configuration:
- Pattern metadata
- ClusterGroup definitions
- Global parameters

#### pattern.sh
Wrapper script for pattern operations:
- Installation
- Upgrade
- Uninstallation
- Validation

#### Makefile
Build targets for:
- Deployment
- Testing
- Validation
- Cleanup

## Additional Resources

- Official Documentation: https://validatedpatterns.io
- Pattern Examples: https://github.com/validatedpatterns
- Community Patterns: https://validatedpatterns.io/patterns/
- Support: Red Hat Customer Portal