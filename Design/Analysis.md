The goal of this project is to analyze an existing repo/project that in some ways uses makefiles, helm charts and ansible to deploy a demo of some functionality.
The analysis should be able to look at at any documentation, makefiles, ansible or helm charts and discover how the project is being deployed.  The initial
project target set will be targeting deploying of the project on top of openshift.  For example, read through the docs and find that the creator has written a
makefile to guide the installation process.  You would analyze the top-level makefile in detail probably starting with an "install" or "deploy" target and follow
the makefile syntax to see all of the deployment steps.  Next, if there are ansible scripts or helm charts that are used as part of the deployment, analyze them
to determine the complete deployment path.  Save what you have learned as both text and a diagram.

The target structure for transformation of this project is a validated pattern.