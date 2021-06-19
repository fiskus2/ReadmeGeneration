# Pyan3

A copy of [Pyan3](https://github.com/Technologicat/pyan) that has been modified in the following way:
* Imports are not displayed in the callgraph
* Calls to functions of indeterminate namespace will not be expanded to calls of all functions with the corresponding name, but remain indeterminate
* An inherited method that has not been overridden is assigned to the namespace of the superclass, rather than the inheriting class
* Fixed incorrect calls to constructors