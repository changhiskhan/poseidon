.. poseidon documentation master file, created by
   sphinx-quickstart on Mon Aug 18 14:34:53 2014.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

********************************
poseidon: tame the digital ocean
********************************

Python library for managing your Digital Ocean account

.. module:: poseidon

**Date**: |today|

**Version**: |version|

.. image:: https://pypip.in/v/poseidon/badge.png
    :target: https://crate.io/packages/poseidon/
    :alt: Latest PyPI version

.. image:: https://pypip.in/d/poseidon/badge.png
    :target: https://crate.io/packages/poseidon/
    :alt: Number of PyPI downloads

The DigitalOcean API allows you to manage Droplets and resources within the
DigitalOcean cloud in a simple, programmatic way using conventional HTTP
requests. The endpoints are intuitive and powerful, allowing you to easily make
calls to retrieve information or to execute actions.

This library starts with a python wrapper for the API and aims to build tools to
make it easier to manage, provision, and deploy to Digital Ocean.

Highlights
==========

- **Full featured**: API wrapper covering the published DigitalOcean API v2

- **Tested**: integration test coverage against most of the API

- **SSH integration**: integrates ``paramiko`` library so you can SSH in and issue commands

- **Deployment conveniences**: methods like ``apt``, ``pip``, and ``git`` for easier deployment


Contents:

.. toctree::
   :maxdepth: 2

   summary
   api
   ssh
