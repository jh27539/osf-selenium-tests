#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Invoke tasks. To run a task, run ``$ invoke <COMMAND>``. To see a list of
commands, run ``$ invoke --list``.
"""

import glob
import logging
import os
import sys

from invoke import task
from selenium import webdriver


logging.getLogger('invoke').setLevel(logging.CRITICAL)

HERE = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
BIN_PATH = os.path.dirname(sys.executable)
bin_prefix = lambda cmd: os.path.join(BIN_PATH, cmd)
MAX_RETRIES = int(os.getenv('MAX_RETRIES', 3))


@task(aliases=['flake8'])
def flake(ctx):
    ctx.run('flake8 .', echo=True)


@task(aliases=['autopep8'])
def autopep(ctx):
    ctx.run('autopep8 .', echo=True)


@task
def clean(ctx, verbose=False):
    ctx.run('find . -name "*.pyc" -delete', echo=True)


@task(aliases=['req'])
def requirements(ctx, dev=False):
    """Install python dependencies.

    Examples:
        invoke requirements
    """

    req_file = os.path.join(HERE, 'requirements.txt')
    cmd = bin_prefix('pip install --exists-action w --upgrade -r {} '.format(req_file))
    ctx.run(cmd, echo=True)


@task
def test_module_wo_exit(ctx, module=None, params=None):
    """Helper for running tests."""
    import pytest

    if params is None:
        params = []

    args = ['-s', '-v', '--tb=short']
    for e in [module, params]:
        if e:
            args.extend([e] if isinstance(e, str) else e)

    print('>>> pytest args: {}'.format(args))
    retcode = pytest.main(args)
    return retcode


@task
def test_module(ctx, module=None, params=None):
    """Helper for running tests."""
    retcode = test_module_wo_exit(ctx, module, params)
    sys.exit(retcode)


@task
def test_selenium_on_prod(ctx):
    """Run Production Smoke Tests on the browser defined by TEST_BUILD."""
    test_selenium_with_retries(
        ctx, 'Production', _get_test_file_list(), module=['-m', 'smoke_test']
    )


@task
def test_two_minute_drill(ctx):
    """Run Two Minute Drill Tests on the browser defined by TEST_BUILD."""
    test_selenium_with_retries(
        ctx,
        'Two Minute Drill',
        _get_test_file_list(),
        module=['-m', 'two_minute_drill'],
    )


@task
def test_core_functionality_part_one(ctx):
    """Run first group of Core Functionality tests on the browser defined by TEST_BUILD."""
    all_test_files = _get_test_file_list()
    midpoint = len(all_test_files) // 2
    file_list = all_test_files[:midpoint]
    test_selenium_with_retries(
        ctx,
        'Core Functionality Part One',
        file_list,
        module=['-m', 'core_functionality'],
    )


@task
def test_core_functionality_part_two(ctx):
    """Run second group of Core Functionality tests on the browser defined by TEST_BUILD."""
    all_test_files = _get_test_file_list()
    midpoint = len(all_test_files) // 2
    file_list = all_test_files[midpoint:]
    test_selenium_with_retries(
        ctx,
        'Core Functionality Part Two',
        file_list,
        module=['-m', 'core_functionality'],
    )


@task
def test_preprints_regression(ctx):
    """Run Preprints related Regression Tests on the browser defined by TEST_BUILD."""
    test_selenium_with_retries(
        ctx,
        'Preprints Regression',
        _get_test_file_list(),
        module=['-k', 'preprint'],
    )


@task
def test_registries_regression(ctx):
    """Run Registries related Regression Tests on the browser defined by TEST_BUILD."""
    # Using 'regist' as keyword since we want to include anything with: 'registries',
    #    'registry', or 'registration'
    test_selenium_with_retries(
        ctx,
        'Registries Regression',
        _get_test_file_list(),
        module=['-k', 'regist'],
    )


@task
def test_meetings_regression(ctx):
    """Run Meetings related Regression Tests on the browser defined by TEST_BUILD."""
    test_selenium_with_retries(
        ctx,
        'Meetings Regression',
        _get_test_file_list(),
        module=['-k', 'meeting'],
    )


@task
def test_institutions_regression(ctx):
    """Run Institutions related Regression Tests on the browser defined by TEST_BUILD."""
    test_selenium_with_retries(
        ctx,
        'Institutions Regression',
        _get_test_file_list(),
        module=['-k', 'institution'],
    )


@task
def test_projects_regression(ctx):
    """Run Projects related Regression Tests on the browser defined by TEST_BUILD."""
    test_selenium_with_retries(
        ctx,
        'Projects Regression',
        _get_test_file_list(),
        module=['-k', 'project'],
    )


@task
def test_collections_regression(ctx):
    """Run Collections related Regression Tests on the browser defined by TEST_BUILD."""
    test_selenium_with_retries(
        ctx,
        'Collections Regression',
        _get_test_file_list(),
        module=['-k', 'collection'],
    )


@task
def test_users_regression(ctx):
    """Run Users related Regression Tests on the browser defined by TEST_BUILD."""
    test_selenium_with_retries(
        ctx,
        'Users Regression',
        _get_test_file_list(),
        module=['-k', 'user'],
    )


@task
def test_other_regression(ctx):
    """Run all other Regression Tests on the browser defined by TEST_BUILD."""
    test_selenium_with_retries(
        ctx,
        'Other Regression',
        _get_test_file_list(),
        module=[
            '-k',
            'not preprint and not regist and not meeting and not institution and not project and not collection and not user',
        ],
    )


@task
def test_all_selenium_part_one(ctx):
    """Run first half of all of the tests on the browser defined by TEST_BUILD."""
    all_test_files = _get_test_file_list()
    midpoint = len(all_test_files) // 2
    file_list = all_test_files[:midpoint]
    test_selenium_with_retries(ctx, 'All Regression Part One', file_list)


@task
def test_all_selenium_part_two(ctx):
    """Run second half of all of the tests on the browser defined by TEST_BUILD."""
    all_test_files = _get_test_file_list()
    midpoint = len(all_test_files) // 2
    file_list = all_test_files[midpoint:]
    test_selenium_with_retries(ctx, 'All Regression Part Two', file_list)


def _get_test_file_list():
    all_test_files = glob.glob('tests/test_*.py')
    all_test_files.sort()
    return all_test_files


@task
def test_selenium_with_retries(ctx, partition_name, file_list, module=None):
    """Run group of tests on the browser defined by TEST_BUILD."""
    flake(ctx)

    # If you want to run any of the invoke tasks locally then uncomment the line below
    # os.environ['TEST_BUILD'] = 'firefox'

    print(
        '>>> Testing {} modules in "/tests/" in {}'.format(
            partition_name, os.environ['TEST_BUILD']
        )
    )
    print('>>> File list for {} is: {}'.format(partition_name, file_list))
    retcode = test_module_wo_exit(ctx, params=file_list, module=module)

    if retcode != 1:
        sys.exit(retcode)

    file_list = ['--last-failed', '--last-failed-no-failures', 'none'] + file_list

    for i in range(1, MAX_RETRIES + 1):
        print(
            '>>> Retesting {} failures, iteration {}, in "/test/" '
            'in {}'.format(partition_name, i, os.environ['TEST_BUILD'])
        )
        retcode = test_module_wo_exit(ctx, params=file_list, module=module)

        if retcode != 1:
            break

    sys.exit(retcode)


@task
def sample_bstack_connectivity(ctx):
    """
    Minimal BrowserStack connectivity check.
    Launches specified browser on BrowserStack and prints page title.
    """
    USERNAME = os.environ.get('BSTACK_USER')
    ACCESS_KEY = os.environ.get('BSTACK_KEY')
    BROWSER = os.environ.get('TEST_BUILD', 'chrome').lower()

    capabilities_map = {
        'chrome': {'browserName': 'Chrome', 'os': 'Windows', 'osVersion': '11'},
        'firefox': {'browserName': 'Firefox', 'os': 'Windows', 'osVersion': '11'},
        'edge': {'browserName': 'Edge', 'os': 'Windows', 'osVersion': '11'},
    }
    capabilities = capabilities_map.get(BROWSER)
    if not capabilities:
        raise ValueError(f'Unsupported browser: {BROWSER}')

    remote_url = f'https://{USERNAME}:{ACCESS_KEY}@hub-cloud.browserstack.com/wd/hub'
    driver = webdriver.Remote(
        command_executor=remote_url, desired_capabilities=capabilities
    )
    driver.get('https://www.example.com')
    print(driver.title)
    driver.quit()
