import pytest
import time
import os
import subprocess

from playwright.sync_api import sync_playwright

from agentlab.analyze import inspect_results
from agentlab.experiments.exp_utils import RESULTS_DIR

#Assumes port 7860 is available
port = os.getenv("AGENTXRAY_APP_PORT", 7860)

@pytest.fixture(scope="module")
def start_subprocess():
    """Starts gradio as a subprocess"""

    process = subprocess.Popen(["agentlab-xray", f"--server_port={port}"])
    time.sleep(5)
    yield process
    process.terminate()
    process.wait()

@pytest.fixture(scope="module")
def start_xray(start_subprocess):
    with sync_playwright() as p:  
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(f'http://127.0.0.1:{port}')  
        yield page
        browser.close()

def test_experiment_dropdown(start_xray):
    """Test if the experiment dropdown is populated with the experiments in the results directory"""

    page = start_xray
    page.get_by_label("Experiment Directory").click()
    page.wait_for_selector("ul.options li", timeout=5000)
    drop_options = page.locator("ul.options li")
    
    exp_dirs = drop_options.all_text_contents()

    #get the experiments from the results directory
    all_summaries = inspect_results.get_all_summaries(RESULTS_DIR, ignore_cache=False, ignore_stale=True)

    #click latest experiment (if present)- setup for the next test
    if len(exp_dirs) > 1:
        drop_options.nth(1).click()

    #ignoring the option '✓ Select Experiment Directory '
    assert len(exp_dirs)-1 == len(all_summaries)


def test_agent_task_seed(start_xray):
    """Test if the agent, task and seed tables are visible"""

    page = start_xray

    agent_tab = page.get_by_role("tab", name="Select Agent")
    agent_tab.click()
    
    page.wait_for_selector("#agent_table", timeout=5000)
    agent_table = page.locator("#agent_table")

    assert agent_table.is_visible()

    task_tab = page.get_by_role("tab", name="Select Task")
    task_tab.click()
    
    page.wait_for_selector("#task_table", timeout=5000)
    task_table = page.locator("#task_table")

    assert task_table.is_visible()

    page.wait_for_selector("#seed_table", timeout=5000)
    seed_table = page.locator("#seed_table")
    
    assert seed_table.is_visible()

    page.wait_for_selector("#profiling_img", timeout=5000)
    profiling = page.locator("#profiling_img")

    assert profiling.is_visible()

def test_for_errors(start_xray):
    """Test if there are any errors in the webpage"""

    page = start_xray

    tabs = page.get_by_role("tab")
    tab_count = tabs.count()
    
    for i in range(tab_count):
        tab = tabs.nth(i)
        tab.click()

        page.wait_for_selector("body", timeout=5000)

        #Finds the error class 
        error_messages = page.locator('.error')
    
        error_count = error_messages.count()
        
        assert error_count == 0
