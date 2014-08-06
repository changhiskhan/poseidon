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
import time
import requests
import simplejson as json

API_VERSION = 'v2'
API_URL = 'https://api.digitalocean.com'


"""
TODO: refactor for multipage results
TODO: unit tests for Images, ImageActions, and DomainRecords
TODO: more tests for droplets
TODO: test account?
"""

class APIError(Exception):

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
        url_components: list or tuple
        """
        url = self.format_request_url(resource, *url_components)
        meth = getattr(requests, kind)
        headers = self.get_request_headers()
        data = self.format_parameters(**kwargs)
        req = meth(url, headers=headers, data=data)
        data = self.get_response(req)
        if req.status_code >= 300:
            msg = data.pop('message', 'API request returned error')
            raise APIError(msg, req.status_code, **data)
        return data

    def get_response(self, req):
        try:
            return req.json()
        except json.JSONDecodeError:
            return {}

    def get_request_headers(self):
        raise NotImplementedError()

    def format_request_url(self, resource, *args):
        raise NotImplementedError()

    def format_parameters(self, **kwargs):
        return kwargs



class DigitalOceanAPI(RestAPI):

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

    name = None

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
        return self.api.send_request(kind, self.name, url_components, **kwargs)

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
        resp = self.get(url_components)
        return resp.get(self.result_key, [])

    @property
    def result_key(self):
        return self.name

    @property
    def singular(self):
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



class DropletActions(Resource):
    """
    Droplet actions are tasks that can be executed on a Droplet. These can be
    things like rebooting, resizing, snapshotting, etc.

    Droplet action requests are generally targeted at the "actions" endpoint
    for a specific Droplet. The specific actions are usually initiated by
    sending a POST request with the action and arguments as parameters.

    Droplet actions themselves create a Droplet actions object. These can be
    used to get information about the status of an action.
    """
    def __init__(self, api, collection, **kwargs):
        super(DropletActions, self).__init__(api)
        self.id = kwargs.pop('id')
        self.parent = collection
        for k, v in kwargs.iteritems():
            if k == 'name':
                k = 'droplet_name'
            setattr(self, k, v)

    @property
    def name(self):
        return 'droplets/%s/actions' % self.id

    def get_action(self, action_id):
        return self.get((action_id,)).get('action')

    def _action(self, type, wait=True, **kwargs):
        result = self.post(type=type, **kwargs)
        if wait:
            self.wait()
        return result

    def reboot(self, wait=True):
        return self._action('reboot', wait)

    def power_cycle(self, wait=True):
        return self._action('power_cycle', wait)

    def shutdown(self, wait=True):
        return self._action('shutdown', wait)

    def power_off(self, wait=True):
        return self._action('power_off', wait)

    def power_on(self, wait=True):
        return self._action('power_on', wait)

    def password_reset(self, wait=True):
        return self._action('password_reset', wait)

    def enable_ipv6(self, wait=True):
        return self._action('enable_ipv6', wait)

    def disable_backups(self, wait=True):
        return self._action('disable_backups', wait)

    def enable_private_networking(self, wait=True):
        return self._action('enable_private_networking', wait)

    def resize(self, size, wait=True):
        return self._action('resize', size=size, wait=wait)

    def restore(self, image, wait=True):
        return self._action('restore', image=image, wait=wait)

    def rebuild(self, image, wait=True):
        return self._action('rebuild', image=image, wait=wait)

    def rename(self, name, wait=True):
        return self._action('rename', name=name, wait=wait)

    def change_kernel(self, kernel_id, wait=True):
        return self._action('change_kernel', kernel=kernel_id, wait=wait)

    def take_snapshot(self, name, wait=True):
        return self._action('snapshot', name=name, wait=wait)

    def kernels(self):
        return self.parent.kernels(self.id)

    def snapshots(self):
        return self.parent.snapshots(self.id)

    def backups(self):
        return self.parent.backups(self.id)

    def actions(self):
        return self.parent.actions(self.id)

    def delete(self, wait=True):
        resp = self.parent.delete(self.id)
        if wait:
            self.wait()
        return resp

    def wait(self):
        """
        wait for all actions to complete on a droplet
        """
        interval_seconds = 5
        while True:
            actions = self.actions()
            slept = False
            for a in actions:
                if a['status'] == 'in-progress':
                    # n.b. gevent will monkey patch
                    time.sleep(interval_seconds)
                    slept = True
                    break
            if not slept:
                break


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
            if k == 'name':
                k = 'image_name'
            setattr(self, k, v)

    def transfer(self, type, region):
        self.post(type=type, region=region)

    @property
    def name(self):
        return 'images/%s/actions' % self.image_id



# ----------------------------------------------------------------------
# Mutable collections
# ----------------------------------------------------------------------

class Droplets(MutableCollection):
    """
    A Droplet is a DigitalOcean virtual machine. By sending requests to the
    Droplet endpoint, you can list, create, or delete Droplets.

    Some of the attributes will have an object value. The region, image, and
    size objects will all contain the standard attributes of their associated
    types. Find more information about each of these objects in their
    respective sections.
    """

    name = 'droplets'

    def kernels(self, id):
        return self._prop(id, 'kernels')

    def snapshots(self, id):
        return self._prop(id, 'snapshots')

    def backups(self, id):
        return self._prop(id, 'backups')

    def actions(self, id):
        return self._prop(id, 'actions')

    def _prop(self, id, prop):
        return super(MutableCollection, self).get((id, prop))[prop]

    def create(self, name, region, size, image, ssh_keys=None,
               backups=None, ipv6=None, private_networking=None, wait=True):
        resp = self.post(name=name, region=region, size=size, image=image,
                         ssh_keys=ssh_keys, backups=backups, ipv6=ipv6,
                         private_networking=private_networking)
        droplet = self.get(resp[self.singular]['id'])
        if wait:
            droplet.wait()
        return droplet

    def get(self, id):
        info = super(Droplets, self).get(id)
        return DropletActions(self.api, self, **info)

    def by_name(self, name):
        for d in self.list():
            if d['name'] == name:
                return self.get(d['id'])
        raise KeyError("Could not find droplet with name %s" % name)

    def update(self, id, **kwargs):
        raise NotImplementedError("Not supported by API")



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
    name = 'images'

    def get(self, id):
        """id or slug"""
        info = super(Images, self).get(id)
        return ImageActions(self.api, **info)



class Keys(MutableCollection):
    """
    DigitalOcean allows you to add SSH public keys to the interface so that you
    can embed your public key into a Droplet at the time of creation. Only the
    public key is required to take advantage of this functionality.
    """

    name = 'account/keys'

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

    name = 'domains'

    def create(self, name, ip_address):
        return (self.post(name=name, ip_address=ip_address)
                .get(self.singular, None))

    def update(self, id, **kwargs):
        raise NotImplementedError()



class DomainRecord(MutableCollection):
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
    def name(self):
        return 'domains/%s/records' % self.domain

    def update(self, id, name):
        return super(Keys, self).update(id, name=name)

    def create(self, type, name=None, data=None, priority=None,
               port=None, weight=None):
        return self.post(type=type, name=name, data=data, priority=priority,
                         port=port, weight=weight)

    def get(self, id, **kwargs):
        return (super(DomainRecord, self).get((id,), **kwargs)
                .get('domain_record', None))



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
    name = 'regions'



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
    name = 'sizes'



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
    name = 'actions'

    def list(self, url_components=()):
        resp = super(Actions, self).get(url_components)
        return resp.get(self.result_key)

    def get(self, id, **kwargs):
        return (super(Actions, self).get((id,), **kwargs)
                .get(self.singular, None))



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
