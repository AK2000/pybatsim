"""
    batsim.sched.resource
    ~~~~~~~~~~~~~~~~~~~~~

    This module provides an abstraction around resources to keep track of allocations.

"""


class Resource:
    """A resource is an introduced abstraction to easier keep track of resource states and
    job allocations.

    :param scheduler: the associated scheduler managing this resource.

    :param batsim_id: the id of this resource.
    """

    def __init__(self, scheduler, batsim_id=-1):
        self._scheduler = scheduler
        self._id = batsim_id
        self._allocated_by = []
        self._previously_allocated_by = []
        self._computing = False

        # TODO: get resource information from Batsim
        self._state = 0
        self._new_state = 0

    @property
    def id(self):
        return self._id

    @property
    def is_allocated(self):
        return bool(self._allocated_by)

    @property
    def allocated_by(self):
        return tuple(self._allocated_by)

    @property
    def previously_allocated_by(self):
        return tuple(self._previously_allocated_by)

    def allocate(self, job, recursive_call=False):
        """Allocate the resource for the given job."""
        assert not self.is_allocated, "Node sharing is currently not allowed"

        if not recursive_call:
            job.reserve(self, recursive_call=True)
        self._allocated_by.append(job)

    def free(self, job, recursive_call=False):
        """Free the resource from the given job."""
        assert job in self._allocated_by, "Job is not allocated on this resource"

        if not recursive_call:
            job.free(self, recursive_call=True)

        self._previously_allocated_by.append((self._scheduler.time, job))
        self._allocated_by.remove(job)

        if not self.is_allocated:
            self.computing = False

    @property
    def state(self):
        return self._state

    @state.setter
    def state(self, value):
        self._new_state = value

    def _do_change_state(self, scheduler):
        scheduler._batsim.set_resource_state([self.id], self._new_state)

    @property
    def computing(self):
        """Whether or not this node is currently computing. As long as one job is still running on this
        node the state will not change."""
        return self._computing

    @computing.setter
    def computing(self, value):
        self._computing = value

    @property
    def resources(self):
        return [self]


class Resources:
    """Helper class implementing parts of the python list API to manage the resources.

       :param from_list: a list of `Resource` objects to be managed by this wrapper.
    """

    def __init__(self, from_list=[]):
        self._resources = list(from_list)

    def allocate(self, job, recursive_call=False):
        """Allocate the job on the whole set of resources."""
        for r in self._resources:
            r.allocate(job, recursive_call=recursive_call)

    def free(self, job, recursive_call=False):
        """Free the job from the whole set of resources."""
        for r in self._resources:
            r.free(job, recursive_call=recursive_call)

    @property
    def resources(self):
        return tuple(self._resources)

    def __add__(self, other):
        """Concatenate two resources lists."""
        return Resources(set(self._resources + other._resources))

    def filter(
            self,
            cond=None,
            sort=None,
            free=False,
            allocated=False,
            limit=None,
            min=None,
            num=None,
            for_job=None):
        """Filter the resources lists to search for resources.

        :param cond: a function evaluating the current resource and returns True or False whether or not the resource should be returned.

        :param sort: a function evaluating the result list prior to limiting the values to sort the results of the filtering.

        :param free: whether or not free resources should be returned.

        :param allocated: whether or not already allocated resources should be returned.

        :param limit: the maximum number of returned resources.

        :param min: the minimum number of returned resources (if less resources are available no resources will be returned at all).

        :param num: the exact number of returned resources.

        :param for_job: for the common case that sufficient resources for a job should be found the exact number of required resources for this particular job are returned. The result can still be filtered with a condition or sorted with a sorting function.
        """
        nr = []

        # Pre-defined filter to find resources for a job submission
        if for_job is not None:
            free = True
            allocated = False
            num = for_job.requested_resources

        # Yield all resources if not filtered
        if not free and not allocated:
            free = True
            allocated = True

        # If a concrete number of resources is requested do not yield less or
        # more
        if num:
            min = num
            limit = num

        # Filter free or allocated resources
        for r in self._resources:
            if r.is_allocated:
                if allocated:
                    nr.append(r)
            else:
                if free:
                    nr.append(r)

        # Filter applying a given condition
        if cond:
            nr2 = nr
            nr = []
            for r in nr2:
                if cond(r):
                    nr.append(r)

        # Sort the resources if a function was given. Resources which should be
        # preferred to be chosen can be sorted to the front of the list.
        if sort:
            nr = sort(nr)

        # Do not yield more resources than requested
        if limit:
            nr = nr[:limit]

        # Do not yield less resources than requested (better nothing than less)
        if min and len(nr) < min:
            nr = []

        # Construct a new resources list which can be filtered again
        return Resources(nr)

    def __len__(self):
        return len(self._resources)

    def __getitem__(self, items):
        return self._resources[items]

    def __delitem__(self, index):
        del self._resources[index]

    def __setitem__(self, index, element):
        self._resources[index] = element

    def __str__(self):
        return str(self._resources)

    def append(self, element):
        self._resources.append(element)

    def remove(self, element):
        self._resources.remove(element)

    def insert(self, index, element):
        self._resources.insert(index, element)

    def __iter__(self):
        return iter(self._resources)
