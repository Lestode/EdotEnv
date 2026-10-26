"""Condition B through Slime's custom data-source and consumer interfaces."""

from slime.data.data_source import RolloutDataSourceWithBuffer

from distillation.policies import DrainBeforePublication


class CompleteResponseDataSource(RolloutDataSourceWithBuffer):
    def register_consumer(self, name, consumer):
        if name != "fully_async":
            raise ValueError("Condition B requires Slime's fully_async consumer")
        super().register_consumer(name, DrainBeforePublication(consumer))
