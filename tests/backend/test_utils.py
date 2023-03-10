import asyncio
import pytest
from dpki.utils import Service


@pytest.mark.asyncio
async def test_srv():
    acc = list()
    srv = Service()

    async def sample1_task():
        await asyncio.sleep(0.02)
        acc.append('SAMPLE1')
        await asyncio.sleep(50)
        acc.append('BAD_END')

    async def sample2_task():
        await asyncio.sleep(0.025)
        acc.append('SAMPLE2')

    async def run():
        srv.create_task(sample1_task())
        srv.create_task(sample2_task())
        assert len(srv.tasks) == 2
        await asyncio.sleep(0.01)
        acc.append('BEGIN')
        await asyncio.sleep(0.05)
        acc.append('END')
        assert len(srv.tasks) == 1
        await srv.stop()
        assert len(srv.tasks) == 0

    await asyncio.gather(srv.start(), run())
    assert len(srv.tasks) == 0
    assert tuple(acc) == ('BEGIN', 'SAMPLE1', 'SAMPLE2', 'END')
