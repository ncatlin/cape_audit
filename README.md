# cape_test
A python module for writing CAPEv2 sandbox test evaluators

This is designed to be used by developers to write tests for CAPE (and their CAPE modules), as well as to be used internally by CAPE to evaluate these tests

Example:

First we create the metadata describing the test and how CAPE will execute it
By executing the same sample with the same parameters, we can narrow down issues to the sandbox or the environment

```python
    
class CapeDynamicTest(CapeDynamicTestBase):
    def __init__(self, test_name, analysis_package):
        super().__init__(test_name, analysis_package)
        self.set_description("Tests API monitoring. " \
        "Runs a series of Windows API calls including file, registry, network and synchronisation.")
        self.set_payload_notes("A single statically linked 64-bit PE binary, tested on Windows 10.")
        self.set_result_notes("These simple hooking tests are all expected to succeed on a correct CAPE setup")
        self.set_zip_password(None)
        self.set_task_timeout_seconds(120)
        self.set_os_targets([OSTarget.WINDOWS])
        self.set_task_config({
              "Route": None,
              "Tags": [ "windows", "exe" ],
              "Request Options": None,
              "Custom Request Params": None,
              "Dump Interesting Buffers": False,
              "Dump Process Memory": False,
              "Trace Syscalls": True,
              "Old Thread Based Loader": False,
              "Unpacker": False,
              "Unmonitored": False,
              "Enforce Timeout": False,
              "AMSI Dumping By Monitor": False,
              "Import Reconstruction": False
          })
        self._init_objectives()
```

Now we describe the test objectives. These can be linear, or relational - so if one fails then all of its descendants will not be evaluated.

```python
    def _init_objectives(self):

        # first and only top-level objective in this test
        # check if there are any behavioural listings at all in the report
        o_has_behaviour_trace = CapeTestObjective(test=self, objective_name="BehaviourInfoGenerated")

        # message for the web UI upon success
        o_has_behaviour_trace.set_success_msg("API hooking is working")

        # message for the web UI upon failure. If you know reasons this might fail
        # then this is the place to write suggestions.
        o_has_behaviour_trace.set_failure_msg("The sample failed to execute, the monitor failed\
                                         to initialise or API hooking is not working")

        # Now add a verifier for the objective. This is an object that returns a state, 
        # message and a dictionary of child states/messages.
        # You can roll your own, but some standard ones are provided.
        # This evaluator simply checks that report.json has a certain key with content
        o_has_behaviour_trace.set_result_verifier(VerifyReportSectionHasContent("behavior"))

        # Now add this objective to the test
        self.add_objective(o_has_behaviour_trace) # top level objective

        # check if it caught the sleep with a specific argument
        o_sleep_hook = CapeTestObjective(test=self, objective_name="DetectSleepTime", is_informational=False)
        o_sleep_hook.set_success_msg("CAPE hooked a sleep and retrieved the correct argument")
        o_sleep_hook.set_failure_msg("There may be a hooking problem/change or the sample failed to run properly")
        # This evaluator checks if the calls list inside the process report has 
        # a sleep call that with parameter 1337
        evaluator = VerifyReportSectionHasMatching(
            path="behavior/processes/calls",
            match_criteria={
                "api": "NtDelayExecution", 
                "arguments/value": "1337"
            })
        o_sleep_hook.set_result_verifier(evaluator)
        # we add it as a child of the 'has behaviour' objective
        o_has_behaviour_trace.add_child_objective(o_sleep_hook)
```