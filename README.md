# simply

A Python framework to test general applications and packages (including Python packages) in any Linux context.

Based on Docker it allows to test code on different distributions, with different services activated and
different versions of interpreter, database or anything else you want to have in your Docker image.

Simply automates the process of building / running a Docker image with appropriate packages, users,
folders configuration files and running services or processes.

It allows to run any code onto purpose built running containers, to check states or properties
 afterwards, and to organize this process into test cases.

TODO
Multiple containers can be ran in parallel, allowing parallelization of tests for speed increase.
