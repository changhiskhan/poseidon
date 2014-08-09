from poseidon.api import (
    API_URL, API_VERSION, DigitalOceanAPI, Actions, Domains,
    Images, Keys, Regions, Sizes)
from poseidon.droplet import Droplets


# ----------------------------------------------------------------------
# API Client
# ----------------------------------------------------------------------

class Client(object):
    """
    The DigitalOcean API allows you to manage Droplets and resources within the
    DigitalOcean cloud in a simple, programmatic way using conventional HTTP
    requests. The endpoints are intuitive and powerful, allowing you to easily
    make calls to retrieve information or to execute actions.

    All of the functionality that you are familiar with in the DigitalOcean
    control panel is also available through the API, allowing you to script the
    complex actions that your situation requires.
    """

    def __init__(self, api_key=None, api_url=API_URL, api_version=API_VERSION):
        self.api = DigitalOceanAPI(api_key, api_url, api_version)
        self.actions = Actions(self.api)
        self.domains = Domains(self.api)
        self.droplets = Droplets(self.api)
        self.images = Images(self.api)
        self.keys = Keys(self.api)
        self.regions = Regions(self.api)
        self.sizes = Sizes(self.api)



def connect(api_key=None, api_url=API_URL, api_version=API_VERSION):
    return Client(api_key, api_url, api_version)
