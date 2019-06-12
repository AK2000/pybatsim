from batsim.batsim import BatsimScheduler, Batsim, Job

import sys
import os
import logging
from procset import ProcSet
from itertools import islice


class FillerSchedWithEvents(BatsimScheduler):

    def __init__(self, options):
        super().__init__(options)


    def onSimulationBegins(self):
        self.nb_completed_jobs = 0

        self.jobs_completed = []
        self.jobs_waiting = []

        self.sched_delay = 0.005

        self.openJobs = set()
        self.availableResources = ProcSet((0,self.bs.nb_compute_resources-1))
        self.unavailableResources = ProcSet()


    def scheduleJobs(self):
        scheduledJobs = []

        #print('openJobs = ', self.openJobs)
        #print('available = ', self.availableResources)

        # Iterating over a copy to be able to remove jobs from openJobs at traversal
        for job in set(self.openJobs):
            nb_res_req = job.requested_resources

            if nb_res_req <= len(self.availableResources):
                # Retrieve the *nb_res_req* first availables resources
                job_alloc = ProcSet(*islice(self.availableResources, nb_res_req))
                job.allocation = job_alloc
                scheduledJobs.append(job)

                self.availableResources -= job_alloc

                self.openJobs.remove(job)

        # update time
        self.bs.consume_time(self.sched_delay)

        # send to uds
        if len(scheduledJobs) > 0:
            self.bs.execute_jobs(scheduledJobs)

        #print('openJobs = ', self.openJobs)
        #print('available = ', self.availableResources)
        #print('')

    def onJobSubmission(self, job):
        self.openJobs.add(job)
        #self.scheduleJobs()

    def onJobCompletion(self, job):
        # Resources used by the job and that are unavailable should not be added to available resources
        p = job.allocation - self.unavailableResources
        self.availableResources |= p
        #self.scheduleJobs()

    def onNotifyEventMachineUnavailable(self, machines):
        self.unavailableResources |= machines
        self.availableResources -= machines

    def onNotifyEventMachineAvailable(self, machines):
        self.unavailableResources -= machines
        self.availableResources |= machines

    def onNotifyGenericEvent(self, event_data):
        pass

    def onNoMoreEvents(self):
        self.scheduleJobs()