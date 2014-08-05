import os
import requests

API_VERSION = 'v2'
API_URL = 'https://api.digitalocean.com'


"""
TODO: refactor for multipage results
"""

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
        return req.json()

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
        header['Authorization'] = 'Bearer: %s' % self.api_key
        return header

    def format_request_url(self, resource, *args):
        """create request url for resource"""
        return '/'.join((self.api_url, self.api_version, resource) + args)



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
        return resp.get(self.name, None)

    @property
    def singular(self):
        return self.name[:-1]



class MutableCollection(ResourceCollection):
    """
    A special type of ResourceCollection whose individual units can be
    retrieved, updated, or deleted
    """

    def delete(self, id):
        return self.delete((id,))

    def update(self, id, **kwargs):
        return self.update((id,), **kwargs)

    def get(self, id, **kwargs):
        return self.get((id,), **kwargs).get(self.singular, None)



class DropletActions(Resource):

    def __init__(self, api, **kwargs):
        super(DropletActions, self).__init__(api)
        self.id = kwargs.pop('id')
        for k, v in kwargs:
            setattr(self, k, v)

    @property
    def name(self):
        return 'droplets/%s/actions' % self.id

    def get_action(self, action_id):
        return self.get((action_id,)).get('action')

    def action(self, type, **kwargs):
        return self.post(type=type, **kwargs)

    def reboot(self):
        return self.action('reboot')

    def power_cycle(self):
        return self.action('power_cycle')

    def shutdown(self):
        return self.action('shutdown')

    def power_off(self):
        return self.action('power_off')

    def power_on(self):
        return self.action('power_on')

    def password_reset(self):
        return self.action('password_reset')

    def enable_ipv6(self):
        return self.action('enable_ipv6')

    def disable_backups(self):
        return self.action('disable_backups')

    def enable_private_networking(self):
        return self.action('enable_private_networking')

    def resize(self, size):
        return self.action('resize', size=size)

    def restore(self, image):
        return self.action('restore', image=image)

    def rebuild(self, image):
        return self.action('rebuild', image=image)

    def rename(self, name):
        return self.action('rename', name=name)

    def change_kernel(self, kernel_id):
        return self.action('change_kernel', kernel=kernel_id)

    def snapshot(self, name):
        return self.action('snapshot', name=name)



class ImageActions(Resource):

    def __init__(self, api, image_id):
        super(ImageActions, self).__init__(api)
        self.image_id = image_id

    def transfer(self, type, region):
        self.post(type=type, region=region)

    @property
    def name(self):
        return 'images/%s/actions' % self.image_id



# Mutable collections

class Droplets(MutableCollection):

    name = 'droplets'

    def kernels(self, id):
        return self.get((id, 'kernels'))['kernels']

    def snapshots(self, id):
        return self.get((id, 'snapshots'))['snapshots']

    def backups(self, id):
        return self.get((id, 'backups'))['backups']

    def actions(self, id):
        return self.get((id, 'actions'))['actions']

    def create(self, name, region, size, image, ssh_keys=None,
               backups=None, ipv6=None, private_networking=None):
        return self.post(name=name, region=region, size=size, image=image,
                         ssh_keys=ssh_keys, backups=backups, ipv6=ipv6,
                         private_networking=private_networking)

    def get(self, id):
        info = self.get((id,)).get(self.singular, None)
        return DropletActions(self.api, info)



class Images(MutableCollection):

    name = 'images'

    def get(self, id, **kwargs):
        """id or slug"""
        return self.get((id,), **kwargs)



class Keys(MutableCollection):

    name = 'account/keys'

    def update(self, id, new_name):
        """id or fingerprint"""
        return super(Keys, self).update(id, name=new_name)

    def create(self, name, public_key):
        return self.post(name=name, public_key=public_key)

    def get(self, id, **kwargs):
        """id or fingerprint"""
        return self.get((id,), **kwargs).get('ssh_key', None)



class Domains(MutableCollection):

    name = 'domains'

    def create(self, name, ip_address):
        return self.post(name=name, ip_address=ip_address)

    def update(self, id, **kwargs):
        raise NotImplementedError()



class DomainRecord(MutableCollection):

    def __init__(self, api, domain):
        self.api = api
        self.domain = domain

    @property
    def name(self):
        return 'domains/%s/records' % self.domain

    def update(self, id, new_name):
        return super(Keys, self).update(id, name=new_name)

    def create(self, type, name=None, data=None, priority=None,
               port=None, weight=None):
        return self.post(type=type, name=name, data=data, priority=priority,
                         port=port, weight=weight)

    def get(self, id, **kwargs):
        return self.get((id,), **kwargs).get('domain_record', None)



# Immutable collections

class Regions(ResourceCollection):

    name = 'regions'



class Sizes(ResourceCollection):

    name = 'sizes'



class Actions(ResourceCollection):

    name = 'actions'

    def get(self, id, **kwargs):
        return self.get((id,), **kwargs).get(self.singular, None)



class Client(object):

    def __init__(self, api_key=None, api_url=API_URL, api_version=API_VERSION):
        self.api = DigitalOceanAPI(api_key, api_url, api_version)
        self.actions = Actions(self.api)
        self.domains = Domains(self.api)
        self.droplets = Droplets(self.api)
        self.images = Images(self.images)
        self.keys = Keys(self.keys)
        self.regions = Regions(self.regions)
        self.sizes = Sizes(self.sizes)



def connect(api_key, api_url=API_URL, api_version=API_VERSION):
    return Client(api_key, api_url, api_version)
