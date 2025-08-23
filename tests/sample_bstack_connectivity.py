import os

from selenium import webdriver


def task_sample_bstack_connectivity(ctx):
    """
    Minimal BrowserStack connectivity check.
    Launches specified browser on BrowserStack and prints page title.
    """
    USERNAME = os.environ.get('BSTACK_USER')
    ACCESS_KEY = os.environ.get('BSTACK_KEY')
    BROWSER = os.environ.get('TEST_BUILD', 'chrome').lower()

    capabilities_map = {
        'chrome': {
            'browserName': 'Chrome',
            'os': 'Windows',
            'osVersion': '11',
        },
        'firefox': {
            'browserName': 'Firefox',
            'os': 'Windows',
            'osVersion': '11',
        },
        'edge': {
            'browserName': 'Edge',
            'os': 'Windows',
            'osVersion': '11',
        },
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
