"""
The DigitalOcean API allows you to manage Droplets and resources within the
DigitalOcean cloud in a simple, programmatic way using conventional HTTP
requests. The endpoints are intuitive and powerful, allowing you to easily make
calls to retrieve information or to execute actions.

All of the functionality that you are familiar with in the DigitalOcean control
panel is also available through the API, allowing you to script the complex
actions that your situation requires.
"""

import os
import requests
import simplejson as json

API_VERSION = 'v2'
API_URL = 'https://api.digitalocean.com'


"""
TODO: refactor for multipage results
TODO: unit tests for Images, ImageActions, and DomainRecords
"""

class APIError(Exception):
    """
    Error raised when API response status code is above 200s range
    """

    def __init__(self, message, status_code, **kwargs):
        super(APIError, self).__init__(message)
        self.status_code = status_code
        for k, v in kwargs.iteritems():
            setattr(self, k, v)



class RestAPI(object):
    """
    Abstract REST API
    """

    def send_request(self, kind, resource, url_components, **kwargs):
        """
        Send a request to the REST API

        Parameters
        ----------
        kind: str, {get, delete, put, post, head}
        resource: str
        url_components: list or tuple to be appended to the request URL

        Notes
        -----
        kwargs contain request parameters to be sent as request data
        """
        url = self.format_request_url(resource, *url_components)
        meth = getattr(requests, kind)
        headers = self.get_request_headers()
        req_data = self.format_parameters(**kwargs)
        response = meth(url, headers=headers, data=req_data)
        data = self.get_response(response)
        if response.status_code >= 300:
            msg = data.pop('message', 'API request returned error')
            raise APIError(msg, response.status_code, **data)
        return data

    def get_response(self, resp):
        """
        Retrieve response as json and deserialize as dict

        Parameters
        ----------
        resp: requests.models.Response
        """
        try:
            return resp.json()
        except json.JSONDecodeError:
            return {}

    def get_request_headers(self):
        raise NotImplementedError()

    def format_request_url(self, resource, *args):
        raise NotImplementedError()

    def format_parameters(self, **kwargs):
        """
        Properly formats array types
        """
        req_data = {}
        for k, v in kwargs.items():
            if isinstance(v, (list, tuple)):
                k = k + '[]'
            req_data[k] = v
        return req_data



class DigitalOceanAPI(RestAPI):
    """
    Implements RestAPI with DigitalOcean API v2 url and authentication method
    """

    def __init__(self, api_key=None, api_url=API_URL, api_version=API_VERSION):
        """
        Parameters
        ----------
        api_key: str, optional
            If not supplied uses value of envvar DIGITALOCEAN_API_KEY
        api_url: str, optional
        api_version: str, optional
        """
        if api_key is None:
            api_key = os.environ.get('DIGITALOCEAN_API_KEY', None)
        if api_key is None:
            raise ValueError("API key was not found nor supplied")
        self.api_key = api_key
        self.api_url = api_url
        self.api_version = api_version

    def get_request_headers(self):
        """
        Format headers for the request
        """
        header = {}
        header['Authorization'] = 'Bearer %s' % self.api_key
        return header

    def format_request_url(self, resource, *args):
        """create request url for resource"""
        return '/'.join((self.api_url, self.api_version, resource) +
                        tuple(str(x) for x in args))



class Resource(object):
    """
    Abstract resource exposed by the REST API
    """

    resource_path = None

    def __init__(self, api):
        """
        Parameters
        ----------
        api: RestAPI
        """
        self.api = api

    def send_request(self, kind, url_components, **kwargs):
        """
        Send a request for this resource to the API

        Parameters
        ----------
        kind: str, {'get', 'delete', 'put', 'post', 'head'}
        """
        return self.api.send_request(kind, self.resource_path, url_components,
                                     **kwargs)

    def get(self, url_components=(), **kwargs):
        """
        Send get request
        """
        return self.send_request('get', url_components, **kwargs)

    def delete(self, url_components=(), **kwargs):
        """
        Send delete request
        """
        return self.send_request('delete', url_components, **kwargs)

    def put(self, url_components=(), **kwargs):
        """
        Send put request
        """
        return self.send_request('put', url_components, **kwargs)

    def post(self, url_components=(), **kwargs):
        """
        Send post request
        """
        return self.send_request('post', url_components, **kwargs)

    def head(self, url_components=(), **kwargs):
        """
        Send head request
        """
        return self.send_request('head', url_components, **kwargs)



class ResourceCollection(Resource):
    """
    A special type of resource that consists of multiple units that can be
    listed
    """

    def list(self, url_components=()):
        """
        Send list request for all members of a collection
        """
        resp = self.get(url_components)
        return resp.get(self.result_key, [])

    @property
    def result_key(self):
        """
        Key value for response contents
        """
        return self.resource_path

    @property
    def singular(self):
        """
        Key value for response contents when requesting single unit of
        collection
        """
        return self.result_key[:-1]



class MutableCollection(ResourceCollection):
    """
    A special type of ResourceCollection whose individual units can be
    retrieved, updated, or deleted
    """

    def delete(self, id):
        return super(MutableCollection, self).delete((id,))

    def update(self, id, **kwargs):
        return self.put((id,), **kwargs)

    def list(self, url_components=()):
        resp = super(MutableCollection, self).get(url_components)
        return resp.get(self.result_key, [])

    def get(self, id, **kwargs):
        """
        Get single unit of collection
        """
        return (super(MutableCollection, self).get((id,), **kwargs)
                .get(self.singular, None))



class ImageActions(Resource):
    """
    Image actions are commands that can be given to a DigitalOcean image.
    In general, these requests are made on the actions endpoint of a specific
    image.

    An image action object is returned. These objects hold the current status
    of the requested action.
    """

    def __init__(self, api, id, **kwargs):
        super(ImageActions, self).__init__(api)
        self.id = id
        for k, v in kwargs.iteritems():
            setattr(self, k, v)

    def transfer(self, region):
        """
        Transfer this image to given region

        Parameters
        ----------
        region: str
            region slug to transfer to (e.g., sfo1, nyc1)
        """
        action = self.post(type='transfer', region=region)['action']
        return self.parent.get(action['resource_id'])

    @property
    def resource_path(self):
        return 'images/%s/actions' % self.id



# ----------------------------------------------------------------------
# Mutable collections
# ----------------------------------------------------------------------

class Images(MutableCollection):
    """
    Images in DigitalOcean may refer to one of a few different kinds of objects.

    An image may refer to a snapshot that has been taken of a Droplet instance.
    It may also mean an image representing an automatic backup of a Droplet.
    The third category that it can represent is a public Linux distribution or
    application image that is used as a base to create Droplets.

    To interact with images, you will generally send requests to the images
    endpoint at /v2/images.
    """
    resource_path = 'images'

    def get(self, id):
        """id or slug"""
        info = super(Images, self).get(id)
        return ImageActions(self.api, parent=self, **info)



class Keys(MutableCollection):
    """
    DigitalOcean allows you to add SSH public keys to the interface so that you
    can embed your public key into a Droplet at the time of creation. Only the
    public key is required to take advantage of this functionality.
    """

    resource_path = 'account/keys'

    @property
    def result_key(self):
        return 'ssh_keys'

    def update(self, id, name):
        """id or fingerprint"""
        return super(Keys, self).update(id, name=name)

    def create(self, name, public_key):
        return (self.post(name=name, public_key=public_key)
                .get(self.singular, None))



class Domains(MutableCollection):
    """
    Domain resources are domain names that you have purchased from a domain
    name registrar that you are managing through the DigitalOcean DNS interface.

    This resource establishes top-level control over each domain. Actions that
    affect individual domain records should be taken on the [Domain Records]
    resource.
    """

    resource_path = 'domains'

    def create(self, name, ip_address):
        """
        Creates a new domain

        Parameters
        ----------
        name: str
            new domain name
        ip_address: str
            IP address for the new domain
        """
        return (self.post(name=name, ip_address=ip_address)
                .get(self.singular, None))

    def records(self, name):
        """
        Get a list of all domain records for the given domain name

        Parameters
        ----------
        name: str
            domain name
        """
        if self.get(name):
            return DomainRecords(self.api, name)

    def update(self, id, **kwargs):
        """
        Domain cannot be updated
        """
        raise NotImplementedError()



class DomainRecords(MutableCollection):
    """
    Domain record resources are used to set or retrieve information about the
    individual DNS records configured for a domain. This allows you to build
    and manage DNS zone files by adding and modifying individual records for a
    domain.
    """

    def __init__(self, api, domain):
        self.api = api
        self.domain = domain

    @property
    def resource_path(self):
        return 'domains/%s/records' % self.domain

    @property
    def singular(self):
        return 'domain_record'

    def rename(self, id, name):
        """
        Change the name of this domain record

        Parameters
        ----------
        id: int
            domain record id
        name: str
            new name of record
        """
        return super(DomainRecords, self).update(id, name=name)[self.singular]

    def create(self, type, name=None, data=None, priority=None,
               port=None, weight=None):
        """
        Parameters
        ----------
        type: str
            {A, AAAA, CNAME, MX, TXT, SRV, NS}
        name: str
            Name of the record
        data: object, type-dependent
            type == 'A' : IPv4 address
            type == 'AAAA' : IPv6 address
            type == 'CNAME' : destination host name
            type == 'MX' : mail host name
            type == 'TXT' : txt contents
            type == 'SRV' : target host name to direct requests for the service
            type == 'NS' :  name server that is authoritative for the domain
        priority:
        port:
        weight:
        """
        if type == 'A' and name is None:
            name = self.domain
        return self.post(type=type, name=name, data=data, priority=priority,
                         port=port, weight=weight)[self.singular]

    def get(self, id, **kwargs):
        """
        Retrieve a single domain record given the id
        """
        return super(DomainRecords, self).get(id, **kwargs)



# ----------------------------------------------------------------------
# Immutable collections
# ----------------------------------------------------------------------

class Regions(ResourceCollection):
    """
    A region in DigitalOcean represents a datacenter where Droplets can be
    deployed and images can be transferred.

    Each region represents a specific datacenter in a geographic location. Some
    geographical locations may have multiple "regions" available. This means
    that there are multiple datacenters available within that area.
    """
    resource_path = 'regions'



class Sizes(ResourceCollection):
    """
    The sizes objects represent different packages of hardware resources that
    can be used for Droplets. When a Droplet is created, a size must be
    selected so that the correct resources can be allocated.

    Each size represents a plan that bundles together specific sets of
    resources. This includes the amount of RAM, the number of virtual CPUs,
    disk space, and transfer. The size object also includes the pricing details
    and the regions that the size is available in.
    """
    resource_path = 'sizes'



class Actions(ResourceCollection):
    """
    Actions are records of events that have occurred on the resources in your
    account. These can be things like rebooting a Droplet, or transferring an
    image to a new region.

    An action object is created every time one of these actions is initiated.
    The action object contains information about the current status of the
    action, start and complete timestamps, and the associated resource type
    and ID.

    Every action that creates an action object is available through this
    endpoint. Completed actions are not removed from this list and are always
    available for querying.
    """
    resource_path = 'actions'

    def list(self, url_components=()):
        resp = super(Actions, self).get(url_components)
        return resp.get(self.result_key)

    def get(self, id, **kwargs):
        return (super(Actions, self).get((id,), **kwargs)
                .get(self.singular, None))
