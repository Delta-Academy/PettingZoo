from ..env import AECIterable, AECIterator
from ..env_logger import EnvLogger
from .base import BaseWrapper


class OrderEnforcingWrapper(BaseWrapper):
    """
    check all call orders:

    * error on getting rewards, dones, infos, agent_selection before reset
    * error on calling step, observe before reset
    * error on iterating without stepping or resetting environment.
    * warn on calling close before render or reset
    * warn on calling step after environment is done
    """

    def __init__(self, env):
        self._has_reset = False
        self._has_rendered = False
        self._has_updated = False
        super().__init__(env)

    def render(self, mode="human", **kwargs):
        if not self._has_reset:
            EnvLogger.error_render_before_reset()
        assert mode in self.metadata["render_modes"]
        self._has_rendered = True
        return super().render(mode, **kwargs)

    def step(self, action):
        if not self._has_reset:
            EnvLogger.error_step_before_reset()
        elif not self.agents:
            self._has_updated = True
            EnvLogger.warn_step_after_done()
            return None
        else:
            self._has_updated = True
            super().step(action)

    def observe(self, agent):
        if not self._has_reset:
            EnvLogger.error_observe_before_reset()
        return super().observe(agent)

    def state(self):
        if not self._has_reset:
            EnvLogger.error_state_before_reset()
        return super().state()

    def agent_iter(self, max_iter=2**63):
        if not self._has_reset:
            EnvLogger.error_agent_iter_before_reset()
        return AECOrderEnforcingIterable(self, max_iter)

    def reset(self, seed=None, return_info=False, options=None):
        self._has_reset = True
        self._has_updated = True
        super().reset(seed=seed, options=options)

    def __str__(self):
        if hasattr(self, "metadata"):
            return (
                str(self.env)
                if self.__class__ is OrderEnforcingWrapper
                else f"{type(self).__name__}<{str(self.env)}>"
            )
        else:
            return repr(self)


class AECOrderEnforcingIterable(AECIterable):
    def __iter__(self):
        return AECOrderEnforcingIterator(self.env, self.max_iter)


class AECOrderEnforcingIterator(AECIterator):
    def __next__(self):
        agent = super().__next__()
        assert (
            self.env._has_updated
        ), "need to call step() or reset() in a loop over `agent_iter`"
        self.env._has_updated = False
        return agent
